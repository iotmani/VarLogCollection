# Var Log Collection 2000
A web service to retrieve and search log files from hosts.

## Usage
To run this web application, you need the `Flask` Python web framework installed:

```
pip install Flask==3.0.3
```

Run the web application:
```
flask --app log_collection.app run --host=0.0.0.0 --port=5100
```


Search for logs after internally exposing the service, e.g.:

http://127.0.0.1:5100/var/log/syslog/syslog.log


## Development
### Running
Run server, with a custom path to logs, and a small number of lines to ease with testing:

```python -m venv .venv && source .venv/bin/activate```

```
LC_MAX_RESULT_LINES=100 LC_VAR_LOG_DIR="`pwd`/tests/logs" \
    flask --app log_collection.app run --port=5100 --debug
```

Note: We use port 5100 as the default 5000 often clashes with a MacOS service.

### Profiling
We can profile the application's core logic using the following:
```
python -m profile -s 'tottime' -m  log_collection.log_reader tests/logs/syslog/syslog.log
```

This will list function calls by total time spent as well as display total number of calls. In other words, hotspots we need to work on.

```

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
  1068707    8.599    0.000   14.870    0.000 :0(read)
  1068689    5.811    0.000    7.011    0.000 :0(seek)
    11557    3.184    0.000   25.065    0.002 log_reader.py:38(get_content)
  1068688    2.633    0.000    5.070    0.000 <frozen codecs>:319(decode)
  1068688    2.437    0.000    2.437    0.000 :0(utf_8_decode)
  1068688    1.201    0.000    1.201    0.000 <frozen codecs>:331(getstate)
  1068687    1.200    0.000    1.200    0.000 <frozen codecs>:335(setstate)
    11556    0.214    0.000    0.214    0.000 :0(print)
        1    0.048    0.048   25.380   25.380 log_reader.py:1(<module>)
        1    0.011    0.011    0.011    0.011 :0(setprofile)
       19    0.004    0.000    0.004    0.000 :0(loads)
    40/11    0.002    0.000    0.008    0.001 _parser.py:512(_parse)
```

### Testing
Unit tests are found under the folder `tests/`. To run unit-tests:
```
python -m unittest
```

You also use `tests/logs/log_collection/log_collection.log` to [view logs from this application](http://127.0.0.1:5100/var/log/log_collection/log_collection.log) for [dogfooding](https://en.wikipedia.org/wiki/Eating_your_own_dog_food).

You can also gunzip `tests/logs/syslog/syslog.log.gz` logs for testing, note that it's not tracked in due to its large size.

### Dependencies
To make code contributions, we recomming using the following packages to provide a consistent development experience:

* `black` for standardizing and auto-formatting any code changes you make in your IDE of choice,
* `coverage` for unit-test coverage reports,
* `mypy` for static type checking based on type-annotations.

```
pip install -r requirements-dev.txt
```

#### Code coverage

```
coverage run --omit '*/.venv/*,*/tests/*' -m unittest
```

Generate test-coverage report (or html):

```
coverage report
Name                           Stmts   Miss  Cover
--------------------------------------------------
archive/__init__.py                0      0   100%
log_collection/__init__.py         0      0   100%
log_collection/app.py             28      0   100%
log_collection/log_reader.py      59     13    78%
log_collection/utils.py           17      0   100%
--------------------------------------------------
TOTAL                            104     13    88%
```

**Mypy for type-checking**

`mypy log_collection`

`Success: no issues found in 4 source files`


Finally, run `deactivate` to exit the virtual environment when done using `deactivate`.


## Architecture
An internal user accesses web applications running on hosts, nginx can sit in between to facilitate routing, potentially add caching etc.

![User to nginx to hosts](architecture.png)



## Out of scope
* Full stack set up, such as the http proxy/load balancer (e.g. nginx), uwsgi (e.g. uvicorn), Kubernetes manifests or VMs Terraform definition
* Caching layer based on usage patterns, or for sharing search results
* Authentication layer
* Removal of sensitive contents (Credit card numbers, emails, PII, HIPAA, GDPR...)
* Folder contents, the user must specify log files by name

## Further improvements
* Forward logs to a central system, with machines as parameters. A log forwarder job sends log events in batches to a message bus to be ingested by a central system, where machines are but another tag to potentially filter by.
* Read larger chunks of text at a time for better IO performance, and adjust if a newline is present
* Pagination based on byte offsets ranges covered, to place sensible limits without compromising on functionality
* Check file contents for zipped, as done by 'file' linux CLI rather than naive file extension