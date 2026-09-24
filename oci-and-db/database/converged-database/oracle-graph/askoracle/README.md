# Ask Oracle Graph and Spatial Visualization Setup

18/09/2026

## When to use this asset?

Use these reusable components to add graph visualization, maps, drawing, browser storage, and spatial analysis to **Ask Oracle Release 5.0.0.1**. This folder contains extensions, not the complete application.

## How to use this asset?

If you have not installed Ask Oracle 5.0.0.1, follow the instructions in the [official Oracle repository](https://github.com/oracle-devrel/oracle-autonomous-database-samples/tree/main/apex/Ask-Oracle-Select-AI-Chatbot/V%205.0.0.1).

1. **Dataset:** use your own data or the district sample in [sampledata/spatial](sampledata/spatial/).
2. **Profile:** review the [Select AI notebook](Profile/Select%20AI.dsnb) and configure it for your schema and data.
3. **App:** follow the [detailed installation and usage guide](AskOracle5.0.0.1/README.md) to assemble the plugins, PL/SQL, JavaScript, and CSS in your app.

The app guide explains each component, installation order, dependencies, testing, and known limitations. Test in a development copy before changing your working app.

## Sample questions

Use the corresponding banking or district dataset and select an AI profile configured for that data.

```text
Which accounts receive the most transfers?
Show transfers from account 406 as a graph
Show transfers from account 934 as a graph
Show all districts and their populations.
```

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0. See [LICENSE.txt](LICENSE.txt). Third-party components retain their respective licenses.
