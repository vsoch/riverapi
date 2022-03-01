.. _getting_started-user-guide:

==========
User Guide
==========

The River API client and specification allows you to easily interact with a `Django River ML <https://github.com/vsoch/django-river-ml>`_ server,
or any other server that imlpements the :ref:`spec`. These servers deploy `river <https://riverml.xyz>`_ online machine learning models.
We are excited about what you might build with this set of tools, and please
`let us know <https://github.com/vsoch/riverapi>`_. if you have a question, find a bug, or want to request a feature!
This is an open source project and we are eager for your contribution. 🎉️

.. _getting_started-user-guide-usage:

Usage
=====

Once you have ``riverapi`` installed (:ref:`getting_started-installation`) you
can interact with server endpoints quite easily in Python.

.. _getting_started-user-guide-usage-client:


Client
------

Creating a client is easy - just import the module and create it.

.. code-block:: python

    from riverapi.main import Client

    # This is the default, just to show how to customize
    cli = Client("http://localhost:8000")


By default, we use localhost and port 8000, and the reason is because this
is the default for a Django application. The above would be equivalent to:


.. code-block:: python

    cli = Client()


And if you had a custom server, "https://ml.land":

.. code-block:: python

    cli = Client("https://ml.land")

You might also want to customize the API prefix, which defaults to "api"


.. code-block:: python

    cli = Client(prefix="ml")

.. _getting_started-user-guide-usage-authentication:


Check
-----

It could be the case that the server is providing multiple endpoints to interact with,
and needs to direct you to the correct one, or merely a different one than before.
If you want to check this, and update the client prefix and/or baseurl with any updates 
from service info, you can do:

.. code-block:: python

    cli.check()


Authentication
--------------

We suggest that most River ML servers support basic authentication, meaning that:

1. The user supplies a username and token in the environment
2. This "basic auth" is added to a base64 encoded header on response 403 with a "Www-Authenticate" response requesting authentication
3. A token is returned that has a scoped lifetime (depending on the server) that can be added to an Authorization bearer token header.

The client here handles this flow for you, and you just need to export your username and token to the environment:

.. code-block:: console

    export RIVER_ML_USER=dinosaur
    export RIVER_ML_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
    
It is up to each server to decide to enforce authentication, and on which views. The client
here will respond appropriately when asked to authenticate the request.

.. _getting_started-user-guide-usage-service-info:

Service Info
------------

Typically you can ping the service info point to see that a server is running a River Online ML
set of endpoints.

.. code-block:: python

    # Basic server info (usually no auth required)
    cli.info()

    {'id': 'django_river_ml',
     'status': 'running',
     'name': 'Django River ML Endpoint',
     'description': 'This service provides an api for models',
     'documentationUrl': 'https://vsoch.github.io/django-river-ml',
     'storage': 'shelve',
     'river_version': '0.9.0',
     'version': '0.0.11'}

There is useful information about the server and river version, and how to find
documentation for the server. In addition, a server that wants to direct the client to a different
baseurl and/or prefix might provide that:

.. code-block:: python

    # Basic server info (usually no auth required)
    cli.info()

    {'baseurl': 'https://prod-server',
     'id': 'django_river_ml',
     'status': 'running',
     'name': 'Django River ML Endpoint',
     'description': 'This service provides an api for models',
     'documentationUrl': 'https://vsoch.github.io/django-river-ml',
     'prefix': 'ml',
     'storage': 'shelve',
     'river_version': '0.9.0',
     'version': '0.0.11'}


.. _getting_started-user-guide-usage-upload-model:


Upload Model
------------

The servers are interacted with via named models. Each named model has a particular flavor (e.g., "regression" or "binary" or "multiclass")
and this flavor is required to provide when you first upload the model to the server. As an example, let's create a simple
regression model.


.. code-block:: python

    from river import linear_model, preprocessing
    from river import preprocessing

    # Upload a model
    model = preprocessing.StandardScaler() | linear_model.LinearRegression()

To upload your model to the server, you need to specify the flavor, and upload!
A successful response (200) will return the model name from the client, which you
will need for other interactions.

.. code-block:: python

    # Save the model name for other endpoint interaction
    model_name = cli.upload_model(model, "regression")
    print("Created model %s" % model_name)
    # Created model fugly-mango


.. _getting_started-user-guide-usage-learning:


Learning
--------

Once the model is created and you have the name, learning is easy!


.. code-block:: python

    from river import datasets
    # Train on some data
    for x, y in datasets.TrumpApproval().take(100):
        cli.learn(model_name, x=x, y=y)


.. _getting_started-user-guide-usage-predicting:

Predicting
----------

And predicting is similar.

.. code-block:: python

    # Make predictions
    for x, y in datasets.TrumpApproval().take(10):
        print(cli.predict(model_name, x=x))

.. _getting_started-user-guide-usage-model-as-json:


Stats and Metrics
-----------------

You can easily ask the server to give you stats or metrics for your model.

.. code-block:: python

    cli.metrics(model_name)
    {'MAE': 7.640048891289847,
     'RMSE': 12.073092099314318,
     'SMAPE': 23.47518046795208}

    cli.stats(model_name)
    {'predict': {'n_calls': 10,
      'mean_duration': 2626521,
      'mean_duration_human': '2ms626μs521ns',
      'ewm_duration': 2362354,
      'ewm_duration_human': '2ms362μs354ns'},
     'learn': {'n_calls': 100,
      'mean_duration': 2684414,
      'mean_duration_human': '2ms684μs414ns',
      'ewm_duration': 2653290,
      'ewm_duration_human': '2ms653μs290ns'}}


Model as Json
-------------

If you need a reminder about your model structure, a helpful function
is to look at it as json.

.. code-block:: python

    # Get the model (this is a json representation)
    model_json = cli.get_model_json(model_name)


Here is an example dumped to json:

.. code-block:: json

    {
        "StandardScaler": {
            "with_std": true
        },
        "LinearRegression": {
            "optimizer": [
                "SGD",
                {
                    "lr": [
                        "Constant",
                        {
                            "learning_rate": 0.01
                        }
                    ]
                }
            ],
            "loss": [
                "Squared"
            ],
            "l2": 0.0,
            "intercept_init": 0.0,
            "intercept_lr": [
                "Constant",
                {
                    "learning_rate": 0.01
                }
            ],
            "clip_gradient": 1000000000000.0,
            "initializer": [
                "Zeros"
            ]
        }
    }

This is for informational purposes only, as you can't do much with it.

.. _getting_started-user-guide-usage-download-model:


Download Model
--------------

To download a pickle of your model, you can use this endpoint:

.. code-block:: python

    cli.download_model(model_name)

By default, it will be called ``<model_name>.pkl`` unless you provide a custom name:

.. code-block:: python

    cli.download_model(model_name, "model.pkl")

.. _getting_started-user-guide-usage-all-models:


All Models
----------

Here is how to list all the model names that the server knows about:


.. code-block:: python

    # Get all models
    print(cli.models())
    {'models': ['doopy-poodle', 'phat-dog', 'tart-gato', 'wobbly-egg']}


.. _getting_started-user-guide-usage-finding-models:


Finding Models
--------------

It's likely that as time passes you'll have a lot of models and not remember which is
which! We can combine a few endpoints discussed above to better look at our models.

.. code-block:: python

    for model in cli.models()['models']:
        print(cli.get_model_json(model))


.. _getting_started-user-guide-usage-streaming:


Streaming Events or Metrics
---------------------------

If you want to watch a server for events (e.g., anything that happens in real like prediction or learning is an event)
or metrics (calculated or updated for a model) you will be interested in streaming endpoints. 

.. code-block:: python

    # Stream events
    for event in cli.stream_events():
        print(event)

    # Stream metrics
    for event in cli.stream_metrics():
        print(event)

Both of the above will hang until you press Control+C or otherwise kill the connection.


Deleting a Model
-----------------

If you want to delete a model:

.. code-block:: python

    cli.delete_model(model_name)


This will delete the model, it's stats, metrics, and flavor. This operation cannot be undone.

This library is under development and we will have more documentation coming soon!
