
$(function() {

    var name, started = false;

    var addUser = function(data, show) {
		user_name = Base64.decode(data.name);
         $("#users").append("<li>" + user_name + "</li>");
        if (show) {
            data.message = 'joins';
            $('#messages').append("<li>" + user_name +": " + data.message+"</li>");
        }
    };

    var removeUser = function(data) {
        $('#user-' + data.id).remove();
        data.message = 'leaves';
        $('#messages').append("<li>" + Base64.decode(data.name) +": " + data.message+"</li>");
    };

    var addMessage = function(data) {
        var d = new Date();
        var win = $(window), doc = $(window.document);
        var bottom = win.scrollTop() + win.height() == doc.height();
        data.time = $.map([d.getHours(), d.getMinutes(), d.getSeconds()],
                          function(s) {
                              s = String(s);
                              return (s.length == 1 ? '0' : '') + s;
                          }).join(':');
                          
        $('#messages').append("<li>("+data.time + ")" + Base64.decode(data.name) +": " + Base64.decode(data.message)+"</li>");
        if (bottom) {
            window.scrollBy(0, 10000);
        }
    };

    $('form').submit(function() {
        var value = Base64.encode($('#message').val());
        if (value) {
            if (!started) {
                name = value;
                data = {room: window.room, action: 'start', name: name};
            } else {
                data = {room: window.room, action: 'message', message: value};
            }
            socket.send(data);
        }
        $('#message').val('').focus();
        return false;
    });

    $('#leave').click(function() {
        location = '/';
    });

    var socket;

    var connected = function() {
        socket.subscribe('room-' + window.room);
        if (name) {
            socket.send({room: window.room, action: 'start', name: name});
        } else {
            showForm();
        }
    };

    var disconnected = function() {
        setTimeout(start, 1000);
    };

    var messaged = function(data) {
        switch (data.action) {
            case 'in-use':
                alert('Name is in use, please choose another');
                break;
            case 'started':
                started = true;
                $('#submit').val('Send');
                $('#users').slideDown();
                $.each(data.users, function(i, name) {
                    addUser({name: name});
                });
                break;
            case 'join':
                addUser(data, true);
                break;
            case 'leave':
                removeUser(data);
                break;
            case 'message':
                addMessage(data);
                break;
            case 'system':
                data['name'] = 'SYSTEM';
                addMessage(data);
                break;
        }
    };

    var start = function() {
        socket = new io.Socket(null,{port:8000,transports:['websocket', 'flashsocket', 'htmlfile', 'xhr-polling', 'jsonp-polling']});
        socket.connect();
        socket.on('connect', connected);
        socket.on('disconnect', disconnected);
        socket.on('message', messaged);
    };

    start();

});
