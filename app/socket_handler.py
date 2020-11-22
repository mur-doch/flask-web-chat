from app import socketio, db
from app.models import Room, User
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from flask import session

default_rooms = ['room1', 'room2', 'room3']

@socketio.on('send message', namespace='/test')
def send_message_handler(message):
    if current_user.is_authenticated:
        # TODO: Should be some kind of error-checking in case this room
        # does not exist.
        room_obj = Room.query.filter_by(id=current_user.current_room).first()
        emit('server message', {'data': current_user.username + ': ' + message['data']}, room=room_obj.name)

@socketio.on('connect', namespace='/test')
def connect_handler():
    # Join room1 by default
    join_room('room1')
    current_user.current_room = 1  
    db.session.commit()
    emit('server message', {'data': current_user.username + ' has connected.'}, room='room1')

@socketio.on('disconnect', namespace='/test')
def disconnect_handler():
    old_room_obj = Room.query.filter_by(id=current_user.current_room).first()
    emit('server message', {'data': current_user.username + ' has disconnected.'}, room=old_room_obj.name)
    print('Client disconnected')
    disconnect_user(old_room_obj.id)

@socketio.on('room change', namespace='/test')
def change_room_handler(message):
    room_name = message['room']
    new_room_obj = Room.query.filter_by(name=room_name).first()
    old_room_obj = Room.query.filter_by(id=current_user.current_room).first()

    if new_room_obj is None:
        emit('server message', {'data': '** This room doesn\'t exist. **'})
        return

    if room_name in default_rooms:
        change_room(new_room_obj.id, old_room_obj.id)
    else:
        password = message['password']
        if new_room_obj.password_hash == "" or new_room_obj.check_password(password):
            change_room(new_room_obj.id, old_room_obj.id)
        else:
            emit('server message', {'data': 
                '** You didn\'t enter the correct password for this room. **'})

@socketio.on('create room', namespace='/test')
def create_room_handler(message):
    room_name = message['room']
    password = message['password']

    if Room.query.filter_by(name=room_name).first() is None:
        new_room_obj = Room(name=room_name, password_hash="", owner_name=current_user.username)
        old_room_obj = Room.query.filter_by(id=current_user.current_room).first()

        if password != "":
            new_room_obj.set_password(password)
        
        db.session.add(new_room_obj)
        db.session.commit()
        
        change_room(new_room_obj.id, old_room_obj.id)
    else:
        emit('server message', {'data': '** This room already exists. **'})

def change_room(new_room, old_room):
    old_room_obj = Room.query.filter_by(id=old_room).first()
    new_room_obj = Room.query.filter_by(id=new_room).first()
    
    leave_room(old_room_obj.name)
    join_room(new_room_obj.name)
    current_user.current_room = new_room_obj.id
    db.session.commit()

    if old_room_obj is not None and old_room_obj.owner_name == current_user.username:
        handle_owner_leaving(old_room_obj.id)
    
    # send room left/joined message
    emit('server message', {'data': current_user.username + ' has left the room.'}, room=old_room_obj.name)
    emit('server message', {'data': current_user.username + ' has joined the room.'}, room=new_room_obj.name)

def disconnect_user(old_id):
    old_room_obj = Room.query.filter_by(id=old_id).first()
    leave_room(old_room_obj.name)
    # set it to room1, by def - can't be left for the close check below
    current_user.current_room = 1 
    db.session.commit()
    if old_room_obj is not None and old_room_obj.owner_name == current_user.username:
        handle_owner_leaving(old_room_obj.id)
        
def handle_owner_leaving(room_id):
    r = Room.query.filter_by(id=room_id).first()
    users_in_room = User.query.filter_by(current_room=r.id).all()
    if len(users_in_room) == 0:
        db.session.delete(r)
    else:
        r.owner_name = users_in_room[0].username
    db.session.commit()
