# River API Client

[![PyPI version](https://badge.fury.io/py/riverapi.svg)](https://badge.fury.io/py/riverapi)

This is an API client created for [django-river-ml](https://pypi.org/project/django-river-ml/)
that is intended to make it easy to interact with an online ML server providing river models (learning, predicting, etc.).
It currently does not provide a terminal  or command line client and is intended to be used
from Python, but if there is a good use case for a command line set of interactions
this can be added.

## Quick Start

Given that you have a server running that implements the same space as django-river-ml, you can do
the following. Note that if your server requires authentication, you can generate a token and export to:

```bash
export RIVER_ML_USER=dinosaur
export RIVER_ML_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

And then do the following example.

```python
from river import datasets
from river import linear_model
from river import preprocessing

from riverapi.main import Client


def main():

    # This is the default, just to show how to customize
    cli = Client("http://localhost:8000")

    # Basic server info (usually no auth required)
    cli.info()

    # Upload a model
    model = preprocessing.StandardScaler() | linear_model.LinearRegression()

    # Save the model name for other endpoint interaction
    model_name = cli.upload_model(model, "regression")
    print("Created model %s" % model_name)

    # Train on some data
    for x, y in datasets.TrumpApproval().take(100):
        cli.learn(model_name, x=x, y=y)

    # Get the model (this is a json representation)
    model_json = cli.get_model_json(model_name)
    model_json

    # Saves to model-name>.pkl in pwd unless you provide a second arg, dest
    cli.download_model(model_name)

    # Make predictions
    for x, y in datasets.TrumpApproval().take(10):
        print(cli.predict(model_name, x=x))

    # Get stats and metrics for the model
    cli.stats(model_name)
    cli.metrics(model_name)

    # Get all models
    print(cli.models())

    # Stream events
    for event in cli.stream_events():
        print(event)

    # Stream metrics
    for event in cli.stream_metrics():
        print(event)

    # Delete the model
    cli.delete_model(model_name)

if __name__ == "__main__":
    main()
```

**under development** more coming soon!

## Contributors

We use the [all-contributors](https://github.com/all-contributors/all-contributors) 
tool to generate a contributors graphic below.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://vsoch.github.io"><img src="https://avatars.githubusercontent.com/u/814322?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Vanessasaurus</b></sub></a><br /><a href="https://github.com/USRSE/usrse-python/commits?author=vsoch" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## TODO

- add spec documentation

## License

This code is licensed under the MPL 2.0 [LICENSE](LICENSE).
