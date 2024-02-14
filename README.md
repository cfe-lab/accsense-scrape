# Accsense Scrape
*Download alarm history from temperature sensors*

To download a year of alarm history, edit `scrape.py` to set the target year.
Either pass the login credentials for the [alarm history pages] through
environment variables, or type them in the code. (Just be sure not to commit
them to Git.) When you run `scrape.py`, the results are written to
`summary.csv`.

[alarm history pages]: https://secure.sensornetworkonline.com/SSIWeb/
