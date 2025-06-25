#!/usr/bin/env python3
r"""
GDELT BigQuery Query Script - JSON Output

This script allows you to query the GDELT (Global Database of Events, Language, and Tone)
public dataset on Google BigQuery and returns results as JSON strings suitable for LLM processing.
All queries are executed under Google Cloud Project 695160383601.

OUTPUT FORMAT:
The script outputs query results as JSON strings representing a list of dictionaries,
where each dictionary corresponds to a row with column names as keys. For example:
[{"Year": 2023, "Actor1Name": "USA", "Count": 150}, {"Year": 2023, "Actor1Name": "CHN", "Count": 120}]

DEPENDENCIES:
Ensure you have the library installed: pip install google-cloud-bigquery

AUTHENTICATION SETUP (REQUIRED):
This script queries the GDELT public dataset, which is hosted on Google BigQuery.
Since GDELT is a public dataset, you only need basic Google Cloud authentication.
The script runs queries under project 695160383601 for billing purposes.

Choose ONE of the following authentication methods:

OPTION A: Application Default Credentials (ADC) - RECOMMENDED
  This method is commonly used for local development.
  
  Steps:
  1. Install Google Cloud SDK (gcloud CLI) if not already installed
  2. Run: gcloud auth application-default login
  3. Follow the browser authentication flow with your Google account
  
  That's it! No special permissions needed since GDELT is a public dataset.
  
  Note: The queries will be billed against project 695160383601, but you don't need
  access to that project since we're only querying public data.

OPTION B: Service Account Key File
  This method uses a service account with a downloaded JSON key file.
  
  Steps:
  1. Create a Google Cloud project (or use an existing one)
  2. Enable the BigQuery API in your project
  3. Create a service account in your project
  4. Download the JSON key file for this service account
  5. Set the environment variable before running this script:
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/keyfile.json"
     
     On Windows Command Prompt:
     set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\keyfile.json
     
     On Windows PowerShell:
     $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\keyfile.json"
  
  Note: The service account doesn't need special permissions since GDELT is public.

USAGE:
  python query_gdelt.py                          # Run with example query menu
  python query_gdelt.py --query "SELECT * FROM ..." # Run custom query
  python query_gdelt.py --example 1              # Run predefined example 1
  python query_gdelt.py --example 2              # Run predefined example 2
  python query_gdelt.py --example 3              # Run predefined example 3
"""

import argparse
import json
import sys
from typing import Optional

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import GoogleCloudError
except ImportError:
    print("ERROR: google-cloud-bigquery library not found.")
    print("Please install it using: pip install google-cloud-bigquery")
    sys.exit(1)

# Google Cloud Project ID for GDELT dataset access
PROJECT_ID = "695160383601"

# Predefined example queries
EXAMPLE_QUERIES = {
    1: {
        "name": "Top Defining Relationships by Year",
        "description": "Find the most frequent actor relationships by year (countries with different country codes)",
        "query": """
SELECT Year, Actor1Name, Actor2Name, event_count FROM (
  SELECT Actor1Name, Actor2Name, Year, COUNT(*) AS event_count,
         RANK() OVER(PARTITION BY YEAR ORDER BY COUNT(*) DESC) AS rank
  FROM (
    SELECT Actor1Name, Actor2Name, Year
    FROM `gdelt-bq.full.events`
    WHERE Actor1Name < Actor2Name
      AND Actor1CountryCode != ''
      AND Actor2CountryCode != ''
      AND Actor1CountryCode != Actor2CountryCode
    
    UNION ALL
    
    SELECT Actor2Name AS Actor1Name, Actor1Name AS Actor2Name, Year
    FROM `gdelt-bq.full.events`
    WHERE Actor1Name > Actor2Name
      AND Actor1CountryCode != ''
      AND Actor2CountryCode != ''
      AND Actor1CountryCode != Actor2CountryCode
  ) combined_actors
  WHERE Actor1Name IS NOT NULL
    AND Actor2Name IS NOT NULL
  GROUP BY Actor1Name, Actor2Name, Year
  HAVING COUNT(*) > 100
)
WHERE rank = 1
ORDER BY Year
LIMIT 20
"""
    },
    2: {
        "name": "Protests in Ukraine Over Time",
        "description": "Track protest events (EventRootCode='14') in Ukraine (ActionGeo_CountryCode='UP') over time",
        "query": """
SELECT MonthYear, CAST(norm*100000 AS INT64)/1000 AS Percent
FROM (
  SELECT ActionGeo_CountryCode, EventRootCode, MonthYear, COUNT(1) AS c,
         COUNT(1) / SUM(COUNT(1)) OVER(PARTITION BY MonthYear) AS norm
  FROM `gdelt-bq.full.events`
  GROUP BY ActionGeo_CountryCode, EventRootCode, MonthYear
)
WHERE ActionGeo_CountryCode='UP' AND EventRootCode='14'
ORDER BY MonthYear
LIMIT 50
"""
    },
    3: {
        "name": "Recent Verbose Events (USA)",
        "description": "Fetch recent events involving USA with comprehensive details including actors, geography, tone, and sources",
        "query": """
SELECT
    GLOBALEVENTID,
    SQLDATE,
    MonthYear,
    Year,
    Actor1Name,
    Actor1CountryCode,
    Actor2Name,
    Actor2CountryCode,
    EventCode,
    EventRootCode,
    EventBaseCode,
    GoldsteinScale,
    NumMentions,
    NumSources,
    NumArticles,
    AvgTone,
    Actor1Geo_Fullname,
    Actor2Geo_Fullname,
    ActionGeo_Fullname,
    ActionGeo_CountryCode,
    SOURCEURL,
    DATEADDED
FROM
    `gdelt-bq.gdeltv2.events`
WHERE
    Actor1CountryCode = 'USA'
    AND DATEADDED IS NOT NULL
    AND SOURCEURL IS NOT NULL
ORDER BY
    DATEADDED DESC
LIMIT 5
"""
    }
}


def initialize_bigquery_client() -> bigquery.Client:
    """
    Initialize BigQuery client for project 695160383601.
    
    Returns:
        bigquery.Client: Configured BigQuery client
        
    Raises:
        GoogleCloudError: If authentication fails or project access is denied
    """
    try:
        print(f"Initializing BigQuery client for project: {PROJECT_ID}")
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test the connection by listing datasets (this will fail if auth is incorrect)
        print("Testing connection...")
        try:
            # Try to access a known public dataset to verify authentication
            datasets = list(client.list_datasets(max_results=1))
            print("✓ Authentication successful")
        except Exception as e:
            print(f"✗ Authentication test failed: {e}")
            raise
            
        return client
    except GoogleCloudError as e:
        print(f"ERROR: Failed to initialize BigQuery client: {e}")
        print("\nPlease ensure:")
        print("1. You have proper authentication set up (see script header for details)")
        print(f"2. Your credentials have access to project {PROJECT_ID}")
        print("3. You have BigQuery User and BigQuery Job User roles")
        raise


def query_to_json(client: bigquery.Client, query: str) -> str:
    """
    Execute a BigQuery query and return results as a JSON string.
    
    Args:
        client: BigQuery client instance
        query: SQL query string to execute
        
    Returns:
        str: JSON string containing query results as a list of dictionaries
        
    Raises:
        GoogleCloudError: If query execution fails
        json.JSONEncodeError: If results cannot be serialized to JSON
    """
    try:
        # Configure query job
        job_config = bigquery.QueryJobConfig()
        job_config.use_query_cache = True
        job_config.use_legacy_sql = False  # Use Standard SQL
        
        # Execute the query
        query_job = client.query(query, job_config=job_config)
        
        # Get the results
        results = query_job.result()
        
        # Convert results to list of dictionaries
        rows_list = []
        for row in results:
            # Convert BigQuery Row to dictionary
            row_dict = dict(row)
            rows_list.append(row_dict)
        
        # Convert to JSON string
        return json.dumps(rows_list, default=str)  # default=str handles non-serializable types
        
    except GoogleCloudError as e:
        # Return error as JSON
        error_result = {"error": f"Query execution failed: {str(e)}"}
        return json.dumps(error_result)
    except Exception as e:
        # Return unexpected error as JSON
        error_result = {"error": f"Unexpected error during query execution: {str(e)}"}
        return json.dumps(error_result)


def execute_query_legacy(client: bigquery.Client, query: str) -> None:
    """
    Legacy function: Execute a BigQuery query and print the results in tabular format.
    This function is kept for reference but not used in the main flow.
    
    Args:
        client: BigQuery client instance
        query: SQL query string to execute
    """
    try:
        print("\nExecuting query...")
        print("=" * 50)
        print(query)
        print("=" * 50)
        
        # Configure query job
        job_config = bigquery.QueryJobConfig()
        job_config.use_query_cache = True
        job_config.use_legacy_sql = False  # Use Standard SQL
        
        # Execute the query
        query_job = client.query(query, job_config=job_config)
        
        print("Query submitted, waiting for results...")
        
        # Get the results
        results = query_job.result()
        
        # Print column headers
        if results.schema:
            headers = [field.name for field in results.schema]
            print("\nQuery Results:")
            print("-" * 80)
            print(" | ".join(f"{header:15}" for header in headers))
            print("-" * 80)
            
            # Print rows
            row_count = 0
            for row in results:
                row_values = []
                for value in row:
                    if value is None:
                        row_values.append("NULL")
                    else:
                        row_values.append(str(value)[:15])  # Truncate long values
                print(" | ".join(f"{value:15}" for value in row_values))
                row_count += 1
                
                # Limit output for very large results
                if row_count >= 100:
                    print(f"\n... (showing first 100 rows, total rows may be more)")
                    break
            
            print("-" * 80)
            print(f"Total rows displayed: {row_count}")
            
            # Show query statistics
            if query_job.total_bytes_processed:
                mb_processed = query_job.total_bytes_processed / (1024 * 1024)
                print(f"Data processed: {mb_processed:.2f} MB")
            if query_job.total_bytes_billed:
                mb_billed = query_job.total_bytes_billed / (1024 * 1024)
                print(f"Data billed: {mb_billed:.2f} MB")
        else:
            print("Query completed successfully (no results returned)")
            
    except GoogleCloudError as e:
        print(f"ERROR: Query execution failed: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error during query execution: {e}")
        raise


def show_example_menu() -> Optional[int]:
    """
    Display available example queries and get user selection.
    
    Returns:
        Selected example number or None if user wants to exit
    """
    print("\nAvailable Example Queries:")
    print("=" * 50)
    
    for num, example in EXAMPLE_QUERIES.items():
        print(f"{num}. {example['name']}")
        print(f"   {example['description']}")
        print()
    
    while True:
        try:
            choice = input(f"Select an example (1-{len(EXAMPLE_QUERIES)}) or 'q' to quit: ").strip().lower()
            
            if choice == 'q':
                return None
            
            choice_num = int(choice)
            if choice_num in EXAMPLE_QUERIES:
                return choice_num
            else:
                print(f"Please enter a number between 1 and {len(EXAMPLE_QUERIES)}")
                
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nExiting...")
            return None


def main():
    """Main function to handle command line arguments and execute queries.
    
    The script now outputs query results as JSON strings, suitable for LLM processing.
    """
    parser = argparse.ArgumentParser(
        description="Query the GDELT public dataset on Google BigQuery - outputs results as JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_gdelt.py --example 1
  python query_gdelt.py --example 2
  python query_gdelt.py --example 3
  python query_gdelt.py --query "SELECT * FROM `gdelt-bq.full.events` LIMIT 10"
  python query_gdelt.py  # Interactive mode with example menu
  
Output Format:
  All queries return results as JSON strings representing a list of dictionaries,
  where each dictionary corresponds to a row with column names as keys.
        """
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Custom SQL query to execute"
    )
    
    parser.add_argument(
        "--example",
        type=int,
        choices=list(EXAMPLE_QUERIES.keys()),
        help=f"Run a predefined example query (1-{len(EXAMPLE_QUERIES)})"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize BigQuery client (suppress verbose output for JSON mode)
        print("Initializing BigQuery client...", file=sys.stderr)
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test the connection silently
        try:
            list(client.list_datasets(max_results=1))
        except Exception as e:
            error_json = json.dumps({"error": f"Authentication failed: {str(e)}"})
            print(error_json)
            sys.exit(1)
        
        # Determine what query to run and execute it
        if args.query:
            # Custom query provided
            result_json = query_to_json(client, args.query)
            print(result_json)
            
        elif args.example:
            # Specific example requested
            example = EXAMPLE_QUERIES[args.example]
            result_json = query_to_json(client, example['query'])
            print(result_json)
            
        else:
            # Interactive mode - show menu
            while True:
                choice = show_example_menu()
                if choice is None:
                    break
                    
                example = EXAMPLE_QUERIES[choice]
                print(f"\nRunning Example {choice}: {example['name']}", file=sys.stderr)
                print(f"Description: {example['description']}", file=sys.stderr)
                
                result_json = query_to_json(client, example['query'])
                print(result_json)
                
                # Ask if user wants to run another query
                try:
                    again = input("\nRun another query? (y/n): ").strip().lower()
                    if again not in ['y', 'yes']:
                        break
                except KeyboardInterrupt:
                    print("\nExiting...", file=sys.stderr)
                    break
        
    except GoogleCloudError as e:
        error_json = json.dumps({"error": f"Google Cloud Error: {str(e)}"})
        print(error_json)
        sys.exit(1)
    except KeyboardInterrupt:
        error_json = json.dumps({"error": "Operation cancelled by user"})
        print(error_json)
        sys.exit(0)
    except Exception as e:
        error_json = json.dumps({"error": f"Unexpected error: {str(e)}"})
        print(error_json)
        sys.exit(1)


if __name__ == "__main__":
    main()