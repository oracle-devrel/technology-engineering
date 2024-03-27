# Oracle Digital Assistant Concierge Template
 
The Concierge Template is a skill for quickly setting up a Knowledge bot.

Concierge Template WebSDK

Setup:
  To use this web-sdk for your bot you minimally need to do the following:
    1. In the scripts/concierge.js file:
        line 3: Enter the URI of your ODA instance in the format shown
        line 5: Enter the channelId of the webchannel you created in ODA
    2. Use the sample index.html or add the following lines in the <head> section of your html-page:
        <script src="scripts/concierge.js" defer></script>
        <script src="scripts/settings.js" defer></script>
        <script src="scripts/web-sdk.js" onload="initSdk('Bots')" defer></script>

Images:
  Under /images you can find all images used by the template; change/overwrite them to your liking

Colors:
  In the colors section (search for 'colors:') of scripts/concierge.js file you can find all html-colorcodes
  Remarks behind each entry explain what the color is used for.
  A few less changed colors are also in style/concierge.css. (search for '#')

Languages:
By default this template uses the language of the browser user profile.
You can change that by adding the language code to the initSdk function in your html page:
  <script src="scripts/web-sdk.js" onload="initSdk('Bots','fr')" defer></script>
In the i18n section (search for 'i18n:') in the scripts/concierge.js file you can add a language section with all translations of texts used by the widget.
You can manage the language menu of the chatwidget with the multiLangChat section (search for 'multiLangChat:') in the scripts/concierge.js file 
In the function getConciergeValues(search for 'function getConciergeValues') in the scripts/concierge.js file you have to check if you need to add your new language section

Passing values to your bot:
In the initUserProfile section (search for 'initUserProfile:') in the scripts/concierge.js file you can add values to be used by your bot. Custom parameters can be added in the profile/properties section.
In your freemarker expression you can use them like profile.properties.value.company (check variables in the skill tester).
 
# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
