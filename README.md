# MLK Archive RAG Application

This repository contains tools for scraping, processing, and exploring the Martin Luther King Jr. Assassination Declassified Records from the National Archives using Retrieval-Augmented Generation (RAG) technology.

## Project Overview

Dr. Martin Luther King Jr.'s legacy is one of courage, justice, and transformation. The declassified records surrounding his assassination (hosted by the National Archives) are a vital part of the historical record. This project aims to make these documents more accessible and searchable using modern AI and data processing technologies.

The project consists of three main components:

1. **Web Scraper**: Scripts to scrape MLK assassination records from the National Archives website
2. **S3 Uploader**: Tools to upload the scraped documents to Amazon S3 for storage
3. **Transforming Archive Documents**: This step was performed using the Unstructured UI to process the PDFs from the National Archives and store them in a ElasticSearch database
3. **RAG Application**: A Jupyter notebook that implements a question-answering system using the processed documents

## Repository Structure

```
.
├── MLK_Archive_RAG_Application.ipynb    # Jupyter notebook with RAG implementation
├── mlk_archive_to_s3/                   # Scripts for scraping and S3 upload
│   ├── download_to_s3.py                # Script to download data to S3
│   ├── scrape_mlk_records.py            # Script to scrape MLK records
│   ├── mlk_records_*.csv                # CSV file with MLK records
│   ├── mlk_records_*.json               # JSON file with MLK records
│   └── mlk_urls_*.txt                   # Text file with MLK URLs
└── mlk_scraper_env/                     # Virtual environment for the project
```

## Data Processing Workflow

The project follows this workflow:

1. **Document Ingestion**: Original documents are scraped from the National Archives and stored in Amazon S3
2. **Document Processing**: Documents are processed using the Unstructured platform with:
   - VLM Partitioning for document segmentation
   - Title-Based Chunking for semantic coherence
   - Named Entity Recognition for metadata enrichment
   - Vector Embedding for semantic search capabilities
3. **Indexing**: Processed documents are indexed in Elasticsearch
4. **RAG Application**: A question-answering system built with LangChain that retrieves relevant document chunks and generates answers

## Setup and Usage

### Prerequisites

- Python 3.13.5
- AWS account with S3 access
- OpenAI API key

### Environment Setup

1. Create a virtual environment:
   ```
   python -m venv mlk_scraper_env
   source mlk_scraper_env/bin/activate 
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `credentials.py` file with your AWS credentials:
   ```python
   ELASTICSEARCH_HOSTS=your-elasticsearch-host
   ELASTICSEARCH_API_KEY=your-elasticsearch-api-key
   ELASTICSEARCH_INDEX_NAME=mlk-archive-public
   OPENAI_API_KEY=your-openai-api-key
   ```


```

### Using the RAG Application

Open and run the Jupyter notebook:

```
jupyter notebook MLK_Archive_RAG_Application.ipynb
```

The notebook contains a question-answering system that allows you to ask questions about the MLK assassination records.

## Acknowledgments

- National Archives for providing access to the declassified MLK assassination records
- LangChain for RAG application framework
