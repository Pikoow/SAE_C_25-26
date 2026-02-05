const url = "https://freemusicarchive.org/file/images/albums/Furchick_-_Rabbits_In_Space_-_2011091972815537.jpg";

const url2 = "https://freemusicarchive.org/file/images/albums/Eleven_Twenty-Nine_-_Eleven_Twenty-Nine_-_20110920150953202.png"

const match = url2.match(/([^/]+\.(jpg|png))$/);
const filename = match ? match[1] : null;


window.open("https://freemusicarchive.org/image/?file=images%2Falbums%2F" + filename + "&width=290&height=290&type=album");