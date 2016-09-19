conformity
==========

A low-level, declarative schema validation library.

Declare a schema::

    person = Dictionary({
        "name": UnicodeString(),
        "height": Float(gte=0),
        "event_ids": List(Integer(gt=0)),
    })

Check to see if data is valid::

    data = {"name": "Andrew", "height": 180.3, "event_ids": [1, "3"]}
    person.errors(data)

    # Key event_ids: Index 1: Not an integer

And wrap functions to validate on the way in and out::

    kwargs = Dictionary({
        "name": UnicodeString(),
        "score": Integer().
    }, optional_keys=["score"])

    @validate_call(kwargs, UnicodeString())
    def greet(name, score=0):
        if score > 10:
            return "So nice to meet you, %s!" % name
        else:
            return "Hello, %s." % name
