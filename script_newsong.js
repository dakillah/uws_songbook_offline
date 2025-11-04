function saveData() {
    var title = document.getElementById('title').value;
    var artist = document.getElementById('artist').value;
    var lyrics = document.getElementById('lyrics').value;
    
    var checkboxes = document.querySelectorAll('.checkboxes input[type="checkbox"]');
    var chords = Array.from(checkboxes).filter(checkbox => checkbox.checked).map(checkbox => checkbox.value);

    var data = {
        title: title,
        artist: artist,
        lyrics: lyrics,
        chords: chords
    };

    var json = JSON.stringify(data);

    // Format the filename as title_artist.json
    var filename = `${title.replace(/\s+/g, ' ')} - ${artist.replace(/\s+/g, ' ')}.json`;

    // For demonstration, we log the JSON data to the console
    console.log(json);

    // To save the JSON data to a file, you can create a blob and download it
    var blob = new Blob([json], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}

function openPreviewTab() {
    var title = document.getElementById('title').value;
    var artist = document.getElementById('artist').value;
    var lyrics = document.getElementById('lyrics').value;

    var checkboxes = document.querySelectorAll('.checkboxes input[type="checkbox"]');
    var chords = Array.from(checkboxes).filter(checkbox => checkbox.checked).map(checkbox => checkbox.value);

    var data = {
        title: title,
        artist: artist,
        lyrics: lyrics,
        chords: chords
    };

    //var json = JSON.stringify(data);
    localStorage.setItem('myData', JSON.stringify(data));

    window.open("preview.html", "_blank");

}
