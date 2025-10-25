const fs = require('fs');
const path = require('path');
const { MongoClient, ServerApiVersion } = require('mongodb');

//const uri = "mongodb+srv://UwsUser:UWSS0ngB00k!@uwssongbookcluster.mlrxi58.mongodb.net/?retryWrites=true&w=majority&appName=uwssongbookcluster";
const uri = "mongodb://127.0.0.1:27017/songlist";
const folderPath = './Songbook'; // Replace with the path to your folder

// Create a MongoClient with a MongoClientOptions object to set the Stable API version
const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  }
});

function listFiles(directoryPath) {
  try {
    const files = fs.readdirSync(directoryPath);
    return files;
  } catch (err) {
    console.error("Error reading directory:", err);
    return [];
  }
}

async function insertFilesToMongoDB(fileList) {
    const client = new MongoClient(uri);

    try {
        await client.connect();
        const db = client.db("songlist");
        const collection = db.collection("scores");

        let ctr=1;
        console.log("Populating scores...BEGIN");
        console.log("..........");
        for (const filePath of fileList) {
            const fileData = fs.readFileSync(path.join(folderPath, filePath), 'utf-8');
            //console.log ("Filedata: ", fileData);
            // Assuming fileData is in JSON format, parse it
            const document = JSON.parse(fileData);
        
            console.log("Inserting document (" + filePath + ")...");

            // Insert the document into the collection
            await collection.insertOne(document);
          
            console.log("Success!");
            console.log("..." + Math.trunc((ctr / fileList.length)*100) + "%");
        
            ctr++;
        }
        console.log("..........");
        console.log("Populating scores...END");
    } catch (err) {
        console.error("Error:", err);
    } finally {
        await client.close();
    }
}

// Example usage:
//const fileList = ['./file1.json', './file2.json', './file3.json']; // Replace with your file paths
const fileList = listFiles(folderPath);

insertFilesToMongoDB(fileList)
    .catch(console.error);
