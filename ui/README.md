# Overview and Thoughts

## What this is

This is a small showcase of a microservices based architecture for the given
ELO Multiplayer League Tracker. Each microservice (API, UI, extendible to
 separate DB) runs in a Docker container, and should be hence easily replaceable,
 movable to a different location, etc. There are pros and cons for microservices,
 and one could certainly argue it is an overkill for this problem space, but then,
 I didn't have enough "user requirements" for this, and I wanted to show my
 reasoning on different levels (architecture, technology choice etc), which makes
 me tend towards more modular architectures.

### The API

The API is written using the [Falcon micro web framework](https://falconframework.org/),
it's one option, there are certainly good alternatives with features like browseable,
self-documenting APIs, but I know this one, and it's quick and "good enough" for
this task. There's no authentication and no api-level versioning, both really
important for real-world issues, but purposely left out for hopefully obvious
reasons.

### The "Business Logics"

The initial code to compute the ELO ratings is nearly untouched (now in
api/ranking.py), except that I removed the user input on entering results with
non-existent players and made it a UI problem (which it should be).

A few lines in there are enforcing Python2, which I would change, but I don't think
it was my task to fiddle with this. It's well written code, except maybe for
this habit to create empty mutable lists and fill them iteratively using
for-loops, here generators would be a better and well readable alternative.

### The Database

I simply chose SQLite because it's very easy to test against it. But as I'm using
SQLAlchemy's ORM on top, it is no effort at all to exchange it for other relational,
more production-typical databases. NoSQL databases would also be an option, a
very good fit would be MongoDB. The database interaction (api/db.py) is encapsulated
from the API layer (api/app.py), it would be easy to exchange this part.

### The UI

Built with Flask, no fancy client side stuff at all. It doesn't come with tests,
it's only there in order to interact with the API in a nicer way. I assume people
will want to build Android or iOS apps instead :-)

## What this not is

This is not a bug-free piece of software, the API/UI layers been built in two
days without specific requirements/wireframes etc. I originally thought I was
not gonna build the UI part but focus on the API to be more robust and tested
(I'm not planning to focus on shiny FE stuff at work),
but eventually I thought it's nicer for an human interaction to have a UI, so
here you go.. :)
