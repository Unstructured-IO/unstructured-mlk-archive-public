# MLK Archive RAG Application

This repository contains tools for scraping, processing, and exploring the Martin Luther King Jr. Assassination Declassified Records from the National Archives using Retrieval-Augmented Generation (RAG) technology.

## Project Overview

Dr. Martin Luther King Jr.'s legacy is one of courage, justice, and transformation. The declassified records surrounding his assassination (hosted by the <a href="https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/transformed-data/mlk-archive-public.jsonl">National Archives</a>) are a vital part of the historical record. This project aims to make these documents more accessible and searchable using modern AI and data processing technologies.

The project consists of these main components:

1. **Web Scraper**: Scripts to scrape MLK assassination records from the National Archives website
2. **S3 Uploader**: Tools to upload the scraped documents to Amazon S3 for storage
3. **Transforming Archive Documents**: This step was performed using the Unstructured UI to process the documents from the National Archives and store them in an ElasticSearch database
4. **RAG Application**: A Jupyter notebook "MLK_Archive_RAG_Application.ipynb" that implements a question-answering system using the processed documents
5. **Release of Processed Results**: The processed data from the MLK archive documents is publicly available via AWS S3 bucket: http://example-transformations-mlk-archive.s3-website-us-east-1.amazonaws.com/

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
└── s3_hosting/                          # Static hosting files
    ├── generate_index.py                # Script to generate index page
    └── index.html                       # Static index page
```

## Data Format

The processed MLK archive documents are available for download:

<p><a href="https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/transformed-data/mlk-archive-public.jsonl">Download mlk-archive-public.jsonl</a></p>

Each line in the JSONL file represents a document element with the following structure:

```json
{
  "element_id": "ab049307ff7695d08f1e798d5372d51b",
  "embeddings": [0.04380892589688301, -0.007506858557462692, -0.013627462089061737, ...],
  "text": "Prefix: This chunk appears near the beginning of an FBI investigation document (File #BH 44-1740) from April 1968 that details inquiries into Eric S. Galt's activities in Birmingham, Alabama...; Original: 1 BH 44-1740 DTD:scb\n\nLAUNDRIES AND CLEANERS, BIRMINGHAM, ALABAMA:...",
  "type": "CompositeElement",
  "record_id": "edb7ea45-00ba-5ab1-a58c-30da4ff50de5",
  "metadata": {
    "filename": "44-at-2386_hs1-852715321_158-01-part_3_of_4.pdf",
    "filetype": "application/pdf",
    "languages": ["eng", "por"],
    "page_number": 1,
    "text_as_html": "<div class=\"Page\" data-page-number=\"1\" />...",
    "orig_elements": "eJztnQtvWzmSqP8KkVngzgB+8P3I9m1AsZXE07Ed2E7vDrYXQZEsxkLLkiHJSecu...",
    "data_source-url": "https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/mlk-archive/44-at-2386_hs1-852715321_158-01-part_3_of_4.pdf",
    "data_source-version": "9940ff50258de939ef2bb1331c7e2fe3-2",
    "data_source-record_locator-protocol": "s3",
    "data_source-record_locator-remote_file_path": "https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/mlk-archive/",
    "data_source-record_locator-metadata-source-url": "https://www.archives.gov/files/research/mlk/releases/2025/0721/44-at-2386_hs1-852715321_158-01-part_3_of_4.pdf",
    "data_source-record_locator-metadata-content-length": "9695272",
    "data_source-record_locator-metadata-download-date": "2025-07-22 15:03:58",
    "data_source-date_created": "1753211039.0",
    "data_source-date_modified": "1753211039.0",
    "data_source-date_processed": "1753223725.6787593",
    "entities-items": [
      {"entity": "FBI", "type": "ORGANIZATION"},
      {"entity": "Eric S. Galt", "type": "PERSON"},
      {"entity": "Birmingham", "type": "LOCATION"},
      {"entity": "Alabama", "type": "LOCATION"}
    ],
    "entities-relationships": [
      {"from": "Eric S. Galt", "relationship": "rented", "to": "Safe Deposit Box No. 5517"},
      {"from": "Eric S. Galt", "relationship": "affiliated_with", "to": "Birmingham Trust National Bank"}
    ]
  }
}
```

### Key Fields:
- **element_id**: Unique identifier for each document element
- **embeddings**: Vector embeddings for semantic search (OpenAI text-embedding-3-large [dim 3072])
- **text**: The processed text content with contextual prefix and original text
- **type**: Element type (e.g., CompositeElement, NarrativeText, Title)
- **record_id**: Unique identifier linking related elements from the same document
- **metadata**: Rich metadata including:
  - Source document information (filename, filetype, page numbers)
  - Processing timestamps and versions
  - Named entities and their relationships
  - Original source URLs from the National Archives
  - HTML representation of the content

## How the MLK Records Were Prepared for Search

> *Note: The steps below were completed prior to this notebook. You do not need to rerun them—they're included here to explain how the records were made searchable.*

The declassified MLK assassination records were processed using the **Unstructured platform** in a multi-step ETL pipeline to make them AI-ready and searchable:

---

#### **Step 1: Document Ingestion into Amazon S3**

- Original documents—including PDFs, images, and other file types—were streamed from the National Archives to **Amazon S3**, providing secure and scalable cloud storage.
   - National Archives: https://www.archives.gov/research/mlk
   - AWS Files: http://example-transformations-mlk-archive.s3-website-us-east-1.amazonaws.com/

---

#### **Step 2: Document Processing with Unstructured**

The Unstructured platform processed each document through a series of enrichment steps:

1. **VLM Partitioning**  
    Vision-Language Models (VLMs) segmented each document into meaningful sections, preserving layout and context. Because most documents were scanned images of typed pages—making OCR challenging—VLMs were chosen for partitioning. Claude 3.7 Sonnet was used as the VLM provider. 

2. **Title-Based Chunking**  
   Documents were split into semantically coherent chunks using structural cues (like section headers) to improve context retention. A "Chunk by Title" chunking strategy with contextual chunking was used. The chunking parameters were:
   ```
   {
   "contextual_chunking": true,
   "combine_text_under_n_characters": 3000,
   "include_original_elements": true,
   "max_characters": 5500,
   "multipage_sections": true,
   "new_after_n_characters": 3500,
   "overlap": 350,
   "overlap_all": true
   }
   ```

3. **Named Entity Recognition (NER)**  
   Entities such as people, organizations, locations, and dates were extracted to enhance downstream filtering and relevance. OpenAI GPT-4o was used with the default NER prompt. For more information about NER, please see our documentation: https://docs.unstructured.io/ui/enriching/ner

4. **Vector Embedding**  
   Each chunk was embedded using OpenAI's `text-embedding-3-large` model (3072 dims), enabling semantic similarity search.

This end-to-end pipeline transformed the raw historical documents into a searchable, structured knowledge base—optimized for natural language queries and intelligent retrieval. Unstructured made it possible to transform 243,496 pages of grainy text in a single day.

---

#### **Step 3: Indexing in Elasticsearch**

- The enriched document chunks—with metadata and vector embeddings—were indexed into **Elasticsearch**, enabling:
  - Fast full-text and semantic (vector) search  
  - Metadata-based filtering and sorting  
  - Scalable querying across large document sets

Access to this database is available using the following credentials:
```
ELASTICSEARCH_HOSTS: "https://mlk-archive-public.es.eastus.azure.elastic-cloud.com"
ELASTICSEARCH_API_KEY: "S0I5ak5aZ0JwcE44OWFmcEpBb3M6dTlpYnVQbk9Ub2dKNk15LUpkT0JwUQ=="
```

---

#### Results
The processed output of the ETL is available via an ElasticSearch database as explained in the Jupyter Notebook "MLK_Archive_RAG_Application.ipynb", or a JSONL copy of the processed data is available for you to download and use for your own research:
- https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/transformed-data/mlk-archive-public.jsonl


## Setup and Usage

### Prerequisites

- Python 3.13.5
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

### Using the RAG Application

Open and run the Jupyter notebook:

```
jupyter notebook MLK_Archive_RAG_Application.ipynb
```

The notebook contains a question-answering system that allows you to ask questions about the MLK assassination records.

## Acknowledgments

- National Archives for providing access to the declassified MLK assassination records
