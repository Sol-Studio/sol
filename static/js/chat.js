var wsUri = "ws://114.207.98.231:3632/";
var output;
count = 0;
live = true;


function init(){
    output = document.getElementById("chat-area");
    testWebSocket();
}


function testWebSocket(){
    websocket = new WebSocket(wsUri);
    websocket.onopen = function(evt){ onOpen(evt) };
    websocket.onclose = function(evt){ onClose(evt) };
    websocket.onmessage = function(evt){ onMessage(evt) };
    websocket.onerror = function(evt){ onError(evt) };
}


function onOpen(evt){
}


function onClose(evt){
}


function onMessage(evt){
    if (evt.data != "fail"){
        writeToScreen(evt.data);
        count++;
    }
}


function onError(evt){
    writeToScreen("<span style='color: red;'>에러 : </span>" + evt.data);
}


function doSend(message){
    websocket.send(message);
}


function writeToScreen(message){
    var pre = document.createElement("p");
    pre.style.wordWrap = "break-word";
    pre.innerHTML = message;
    output.appendChild(pre);
}


function closeTab(){
    websocket.close(1000);
    window.close();
}


$('.chat-input input').keyup(function(e) {
    if ($(this).val() == '') $(this).removeAttr('good');
    else $(this).attr('good', '');
});


$("#send_input").keydown(function(e){
    if (e.keyCode == 13) send_msg()
});


function send_msg(){
    doSend("s{'userid': '{{ userid }}', 'room': '{{ room }}', 'content': '" + document.getElementById('send_input').value + "'}");
    document.getElementById('send_input').value = "";
}


function switchLive(){
    live = !live;
    if (live){
        $('#live_update').html("<div style='color: green;'>실시간 업데이트 활성화됨</div>");
    }
    else{
        $('#live_update').html("<div style='color: red;'>실시간 업데이트 비활성화됨</div>");
    }
}


setInterval(function() { if (live) doSend("l{'userid': '{{ userid }}', 'room': '{{ room }}', 'id': " + count + "}"); }, 1000);
window.addEventListener("load", init, false);
