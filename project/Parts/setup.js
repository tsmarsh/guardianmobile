
var dashcodePartSpecs = {
    "articleDate": { "creationFunction": "CreateText", "text": "Publish Date" },
    "articleDescription": { "creationFunction": "CreateText", "text": "Article" },
    "articleTitle": { "creationFunction": "CreateText", "text": "Title" },
    "backToHeadlines": { "creationFunction": "CreatePushButton", "initialHeight": 30, "initialWidth": 140, "leftImageWidth": 16, "rightImageWidth": 5, "text": "Back to Articles" },
    "footer": { "creationFunction": "CreateText", "text": "guardian.co.uk © Guardian News and Media Limited 2009 Registered in England and Wales. No. 908396. Registered office: Number 1 Scott Place, Manchester M3 3GG" },
    "headlineDescription": { "creationFunction": "CreateText", "text": "Article Description" },
    "headlineList": { "creationFunction": "CreateList", "dataArray": ["Article Title", "Item 2", "Item 3"], "dataSourceName": "headlineList", "labelElementId": "headlineTitle", "listStyle": "List.EDGE_TO_EDGE", "sampleRows": 2, "useDataSource": true },
    "headlineTitle": { "creationFunction": "CreateText", "text": "Article Title" },
    "readMore": { "creationFunction": "CreatePushButton", "initialHeight": 30, "initialWidth": 140, "leftImageWidth": 5, "rightImageWidth": 16, "text": "Read More" },
    "secondHeadlines": { "creationFunction": "CreateList", "dataArray": ["Item 1", "Item 2", "Item 3"], "dataSourceName": "secondHeadlineList", "labelElementId": "secondHeadlineTitle", "listStyle": "List.EDGE_TO_EDGE", "sampleRows": 2, "useDataSource": true },
    "secondHeadlineTitle": { "creationFunction": "CreateText", "text": "Article Title" },
    "StackLayout": { "creationFunction": "CreateStackLayout", "subviewsTransitions": [{ "direction": "right-left", "duration": "", "timing": "ease-in-out", "type": "push" }, { "direction": "right-left", "duration": "", "timing": "ease-in-out", "type": "push" }] },
    "todaysDate": { "creationFunction": "CreateText", "text": "DATE" }
};
