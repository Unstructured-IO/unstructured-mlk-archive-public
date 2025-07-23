#!/usr/bin/env python3
"""
Script to download MLK archive files and upload them to S3
"""

import requests
import boto3
from botocore.config import Config
import os
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from credentials import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET,
    AWS_SESSION_TOKEN
)

config = Config(max_pool_connections=50)  # Increase from the default of 10

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLKArchiveDownloader:
    def __init__(self, s3_bucket_name, aws_profile=None, max_workers=5):
        """
        Initialize the downloader
        
        Args:
            s3_bucket_name: Name of the S3 bucket to upload to
            aws_profile: AWS profile to use (optional)
            max_workers: Number of concurrent downloads
        """
        self.s3_bucket_name = s3_bucket_name
        self.max_workers = max_workers
        
        # Initialize S3 client with imported credentials
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
            self.s3_client = session.client('s3')
        else:
            # Use imported credentials
            session_kwargs = {
                'aws_access_key_id': AWS_ACCESS_KEY_ID,
                'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
                'region_name': AWS_REGION
            }
            if AWS_SESSION_TOKEN:
                session_kwargs['aws_session_token'] = AWS_SESSION_TOKEN
            
            self.s3_client = boto3.client('s3', config=config, **session_kwargs)
        
        # Initialize requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        self.downloaded_count = 0
        self.failed_count = 0
        self.total_size = 0
    
    def download_and_upload_file(self, url, s3_key_prefix="mlk-archive/"):
        """
        Download a file from URL and upload directly to S3
        
        Args:
            url: URL to download from
            s3_key_prefix: Prefix for S3 key
        
        Returns:
            tuple: (success, filename, error_message)
        """
        try:
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            s3_key = f"{s3_key_prefix}{filename}"

            # Get expected remote file size
            try:
                head_response = self.session.head(url, timeout=10)
                head_response.raise_for_status()
                remote_size = int(head_response.headers.get('content-length', 0))
            except requests.RequestException as e:
                error_msg = f"Failed to fetch headers for {filename}: {str(e)}"
                logger.error(error_msg)
                self.failed_count += 1
                return False, filename, error_msg

            # Check if file already exists in S3 and matches size
            try:
                obj = self.s3_client.head_object(Bucket=self.s3_bucket_name, Key=s3_key)
                s3_size = obj.get('ContentLength', -1)

                if s3_size == remote_size:
                    logger.info(f"File {filename} already exists in S3 and matches size, skipping.")
                    return True, filename, "Already exists and matches size"
                else:
                    logger.info(f"File {filename} exists but size differs (S3: {s3_size}, Remote: {remote_size}), re-downloading.")
            except self.s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise  # Other errors are real problems

            # Download file
            logger.info(f"Downloading {filename}...")
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Use BytesIO to buffer the content
            from io import BytesIO
            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                buffer.write(chunk)
            buffer.seek(0)  # Reset position to beginning of buffer
            
            # Get actual size of the buffer
            buffer_size = buffer.getbuffer().nbytes
            logger.info(f"Downloaded {filename} ({buffer_size} bytes)")

            # Upload to S3 using the buffered content
            self.s3_client.upload_fileobj(
                buffer,
                self.s3_bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': self.get_content_type(filename),
                    'Metadata': {
                        'source_url': url,
                        'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'content_length': str(buffer_size)  # Use actual buffer size
                    }
                }
            )

            self.downloaded_count += 1
            self.total_size += buffer_size  # Use buffer_size instead of remote_size
            logger.info(f"Successfully uploaded {filename} to S3 ({buffer_size} bytes)")
            return True, filename, None
            
        except requests.RequestException as e:
            error_msg = f"Download error: {str(e)}"
            logger.error(f"Failed to download {url}: {error_msg}")
            self.failed_count += 1
            return False, filename, error_msg
            
        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            logger.error(f"Failed to upload {filename}: {error_msg}")
            self.failed_count += 1
            return False, filename, error_msg
    
    def get_content_type(self, filename):
        """Get content type based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.mp3': 'audio/mpeg',
            '.txt': 'text/plain',
            '.json': 'application/json'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def download_from_url_file(self, url_file_path):
        """
        Download all URLs from a text file
        
        Args:
            url_file_path: Path to file containing URLs (one per line)
        """
        # Read URLs from file
        with open(url_file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        total_urls = len(urls)
        logger.info(f"Starting download of {total_urls} files to S3 bucket: {self.s3_bucket_name}")
        
        # Create S3 bucket if it doesn't exist
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
        except self.s3_client.exceptions.ClientError:
            logger.info(f"Creating S3 bucket: {self.s3_bucket_name}")
            self.s3_client.create_bucket(Bucket=self.s3_bucket_name)
        
        # Download files concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_url = {
                executor.submit(self.download_and_upload_file, url): url 
                for url in urls
            }
            
            # Process completed downloads
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, filename, error = future.result()
                    if success:
                        progress = (self.downloaded_count / total_urls) * 100
                        logger.info(f"Progress: {self.downloaded_count}/{total_urls} ({progress:.1f}%)")
                    else:
                        logger.error(f"Failed: {filename} - {error}")
                except Exception as e:
                    logger.error(f"Unexpected error processing {url}: {str(e)}")
        
        # Print summary
        logger.info(f"\nDownload Summary:")
        logger.info(f"Total files: {total_urls}")
        logger.info(f"Successfully downloaded: {self.downloaded_count}")
        logger.info(f"Failed downloads: {self.failed_count}")
        logger.info(f"Total size downloaded: {self.total_size / (1024*1024):.2f} MB")
        logger.info(f"Files uploaded to S3 bucket: {self.s3_bucket_name}")

def run_mlk_download():
    """
    Run the MLK archive download using imported credentials
    """
    url_file = "mlk_urls_20250722_133807.txt"
    
    # Create downloader with imported credentials
    downloader = MLKArchiveDownloader(
        s3_bucket_name=S3_BUCKET,
        max_workers=5
    )
    
    # Start download
    downloader.download_from_url_file(url_file)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download MLK archive files to S3')
    parser.add_argument('url_file', help='Path to file containing URLs')
    parser.add_argument('s3_bucket', help='S3 bucket name')
    parser.add_argument('--aws-profile', help='AWS profile to use')
    parser.add_argument('--max-workers', type=int, default=5, help='Number of concurrent downloads')
    parser.add_argument('--s3-prefix', default='mlk-archive/', help='S3 key prefix')
    
    args = parser.parse_args()
    
    # Create downloader
    downloader = MLKArchiveDownloader(
        s3_bucket_name=args.s3_bucket,
        aws_profile=args.aws_profile,
        max_workers=args.max_workers
    )
    
    # Start download
    downloader.download_from_url_file(args.url_file)

if __name__ == "__main__":
    # If no command line arguments, run with imported credentials
    import sys
    if len(sys.argv) == 1:
        run_mlk_download()
    else:
        main()
