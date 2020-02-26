# Qmobi_test_task

To run server, you must run **server.py**

Some setting are located at **config.py**
**PORT** - value on which port the server will start
**LOG_LEVEL** - customisation log info: 
* 1 - print only errors; 
* 2 - print errors and log messages; 
* 3 - print errors, log and debug messages. 

Some test are located at **tests.py**

Server get valute data from <http://cbr.ru/>

Example request: http://localhost:53210/converter?valute=USD&value=300
Example response:
```json
{
    "valute": "USD",
    "rate": 64.9213,
    "rate_date": "26.02.2020",
    "req_value": "USD",
    "res_value": 19476.39
}
```
