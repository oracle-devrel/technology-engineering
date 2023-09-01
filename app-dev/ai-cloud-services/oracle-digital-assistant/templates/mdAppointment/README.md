Sample ODA Appointment booking flow

This sample flow 'Appointment' contains a few reusable constructs/learnings:
- Resolving dependancies of inputs
- Skipping inputs because of more detailed inputs already known
- Mixing questions and Composite Bag
- Value-lists wih synonyms


In this example there are hospitals in cities.
When a hospital is given, the city is known
When a city is specified/given, only hospitals in that city are available
When a city has only one hospital, this hospital is known
