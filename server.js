const express = require('express');
const app = express();

const cors = require('cors');
app.use(cors());

const port = process.env.PORT || 3001;

const { MongoClient, ServerApiVersion } = require('mongodb');
//const uri = "mongodb+srv://UwsUser:UWSS0ngB00k!@uwssongbookcluster.mlrxi58.mongodb.net/?retryWrites=true&w=majority&appName=uwssongbookcluster";
const uri = "mongodb://127.0.0.1:27017/songlist";

// Create a MongoClient with a MongoClientOptions object to set the Stable API version
/*
const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  }
});
*/
const client = new MongoClient(uri);

app.get('/listAllSongs', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryTitle = req.query.title;

    const queryRes = await collection.find().sort({ title : 1 }).toArray();

    res.json(queryRes);
})

app.get('/listArtists', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryRes = await collection.distinct( "artist" );

    res.json(queryRes);
})

app.get('/listDistinctArtists', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryTitle = req.query.title;

    const queryRes = await collection.distinct( "artist", { title : queryTitle });

    res.json(queryRes);
})

app.get('/listTitles', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryRes = await collection.distinct( "title" );

    res.json(queryRes);
})

app.get('/listDistinctTitles', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryArtist = req.query.artist;

    const queryRes = await collection.distinct( "title", { artist : queryArtist });

    res.json(queryRes);
})

app.get('/getLyrics', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("scores");

    const queryArtist = req.query.artist;
    const queryTitle = req.query.title;


    console.log("getLyrics?artist=" + queryArtist + "&title=" + queryTitle);

    const queryRes = await collection.findOne({ artist : queryArtist, title : queryTitle });

    console.log("queryRes=", queryRes);

    res.json(queryRes);
})

app.get('/listAllSongsTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryTitle = req.query.title;

    const queryRes = await collection.find().sort({ title : 1 }).toArray();

    res.json(queryRes);
})

app.get('/listArtistsTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryRes = await collection.distinct( "artist" );

    res.json(queryRes);
})

app.get('/listDistinctArtistsTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryTitle = req.query.title;

    const queryRes = await collection.distinct( "artist", { title : queryTitle });

    res.json(queryRes);
})

app.get('/listTitlesTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryRes = await collection.distinct( "title" );

    res.json(queryRes);
})

app.get('/listDistinctTitlesTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryArtist = req.query.artist;

    const queryRes = await collection.distinct( "title", { artist : queryArtist });

    res.json(queryRes);
})

app.get('/getLyricsTest', async function (req, res)
{
    const db = client.db("songlist");
    const collection = db.collection("test_scores");

    const queryArtist = req.query.artist;
    const queryTitle = req.query.title;


    console.log("getLyrics?artist=" + queryArtist + "&title=" + queryTitle);

    const queryRes = await collection.findOne({ artist : queryArtist, title : queryTitle });

    console.log("queryRes=", queryRes);

    res.json(queryRes);
})

var server = app.listen(port, function () 
{
    client.connect();

    console.log(`Server is running on http://localhost:${port}`);
})

