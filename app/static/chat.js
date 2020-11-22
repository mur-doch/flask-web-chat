$(document).ready(function() {
	var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');
	
	socket.on('server message', function(msg) {
		$('#message_log').append('<p>' + msg.data + '</p>');
		$('#message_log').scrollTop($('#message_log').prop('scrollHeight'));
	});
	
	$('form#send_message_form').submit(function(event) {
		console.log("SEND MESSAGE");
		socket.emit('send message', {data: $('#message_text').val()});
		$('#message_text').val("");
		return false;
	});

	$('#connect_link').on('click', function(e) {
		e.preventDefault();
		if (socket.disconnected) {
			socket.open();
			$('#connect_link').css('display', 'none');
			$('#disconnect_link').css('display', 'inline');
		}
	});

	$('#disconnect_link').on('click', function(e) {
		e.preventDefault();
		if (socket.connected) {
			socket.close();
			$('#connect_link').css('display', 'inline');
			$('#disconnect_link').css('display', 'none');
		}
	});

	$('#rooms').change(function () {
		socket.emit('room change', {room: $('#rooms').val()});
	});

	$('#create_room_form').submit(function (e) {
		e.preventDefault();
		let roomName = $('#create_room_name').val().trim();
		let password = $('#create_room_password').val();
		if (roomName !== "") {
			socket.emit('create room', {room: roomName, password: password});
			$('#create_room_name').val('');
			$('#create_room_password').val('');
		}
	});

	$('#join_room_form').submit(function (e) {
		e.preventDefault();
		let roomName = $('#join_room_name').val().trim();
		let password = $('#join_room_password').val();
		if (roomName !== "") {
			socket.emit('room change', {room: roomName, password: password});
			$('#join_room_name').val('');
			$('#join_room_password').val('');
		}
	});
});
