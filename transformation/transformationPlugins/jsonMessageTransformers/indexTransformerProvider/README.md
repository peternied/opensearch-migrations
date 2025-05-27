# Configuration Routing


```json
[
  {
    "IndexTransformerProvider": {
      "settings": [
         {
            "indexPattern": "myIndex*",
            "updateSetting": {
                "index": {
                    "number_of_shards": 2
                }
            }
         },
         {
            "indexPattern": "*",
            "remoteSetting": {
                "index": {
                    "lifecycle": {
                        "name": "removeMe"
                    }
                }
            }
         }
      ],
      "mappings": [
        {
            "indexPattern": "*",
            "typeNamePattern": "flatten",
            "replaceType": {
                "type": "flat_object",
            },
            "clearOtherFields": true
        },
        {
            "indexPattern": "*",
            "typeNamePattern": "constant_keyword",
            "replaceType": {
                "type": "keyword",
                
            },
            "clearOtherFields": true
        }
      ]
    }
  }
]
```