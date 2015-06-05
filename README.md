Poliglo
=======


## Server (mastermind)

### Install

	pip install -r requirements.txt


### Start

	CONFIG_PATH=<absolute_path>/config.conf \
	SCRIPTS_PATH=<absolute_path>/scripts:<absolute_path>/scripts_other \
	python master_mind.py

To start the mastermind we need to provide the config file and the paths to scripts

##### CONFIG_PATH
Example file:

```json
{
    "all": {
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": 6379,
        "REDIS_DB": 0,
        "POLIGLO_SERVER_URL": "http://localhost:9015"
    },
    "upload_file_s3": {
        "S3_ACCESS_KEY": "XXXX",
        "S3_SECRET_KEY": "XXX"
    }
}
```

Where the keys of the file are the name of the worker (or "all" to affect all workers). So with "upload_file_s3" we are giving a specific configuration for the worker "upload_file_s3"

##### SCRIPTS_PATH

Path separeted by : this paths should contains files starting with script_

Example script file:

    {
        "id": "crawl_parcelas",
        "name": "Crawl parcelas",
        "start_worker": "crawl_list_of_elements",
        "group": "personal",
        "workers": {
            "crawl_list_of_elements": {
                "default_inputs": {
                    "url": "http://www.yapo.cl/ohiggins/todos_los_avisos?ca=7_s&l=0&q=hectarea&w=1",
                    "next_page_selector": "//div[@class='resultcontainer']//a[contains(text(), 'Próxima página')]/@href",
                    "element_selector": "tr.listing_thumbs",
                    "extract_data": {
                        "image": ".link_image img@src",
                        "price": ".price",
                        "category": ".category",
                        "region": ".region",
                        "sector": ".commune",
                        "name": "a.title",
                        "url": "a.title@href"
                    }
                },
                "outputs": ["filter_prop"]
            },
            "filter_prop": {
                "default_inputs": {
                    "min_price": 0,
                    "max_price": 50000000
                },
                "outputs": ["wait_jobs"]
            },
            "wait_jobs": {
                "default_inputs": {
                    "wait_jobs_from": ["crawl_list_of_elements", "filter_prop"]
                },
                "outputs": ["write_queue_to_file"]
            },
            "write_queue_to_file": {
                "default_inputs": {
                    "target_file": "/tmp/datos.json"
                },
                "outputs": ["upload_file_s3"]
            },
            "upload_file_s3": {
                "default_inputs": {
                    "file_to_upload": "/tmp/datos.json",
                    "target_filename": "parcelas.json",
                    "target_bucket": "poliglo",
                    "read_option": "r"
                }
            }
        }
    }
