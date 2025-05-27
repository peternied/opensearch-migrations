function main(context) {
    console.log("Context: ", JSON.stringify(context, mapToPlainObjectReplacer, 2));
    if (!context) {
        throw new Error('No configuration for index transformer is available.');s
    }

    return (document) => {
        if (document?.has("type") && document?.has("name") && document?.has("body")) {
            // It might be a metadata request, lets try to update it.
        }

        return document;        
    };
}

(() => main)()