$(document).ready(function () {
    // TODO: update all defaultgame references
    // TODO: add separate sockets for each of the game comms
    var socket = io({ autoconnect: true });
    let username = document.getElementById('username');
    let question = document.getElementById('question');

    let game_start_btn = document.getElementById('game_start');
    let game_pause_btn = document.getElementById('game_pause');
    let game_reset_btn = document.getElementById('game_reset');

    if (localStorage.getItem("username") == null |
        localStorage.getItem("username") == "") {
        let default_username = 'Not_a_wolf_' + Math.floor(Math.random() * 10000 % 9999);
        username.defaultValue = default_username;
        localStorage.setItem('username', default_username);
    } else {
        username.defaultValue = localStorage.getItem("username");
    }
    var user = username.value;
    var game_status = document.getElementById('game_status');
    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('game_state', function (game_state) {
        game_status.value = game_state;
        console.log(game_state);
    });

    $('#question_submit').on('click', function () {
        console.log('emitting question: ' + question.value);
        if (question.value != "") {
            socket.emit('question', '[' + user + ']: ' + question.value);
        }
    });
    $('#game_start').on('click', game_start_resume);
    $('#game_pause').on('click', game_pause);
    $('#game_reset').on('click', game_reset);
    function game_start_resume() {
        console.log('Attempting to start game');
        socket.emit('game_start', 'defaultgame');
        game_start_btn.innerText = 'Start game'
        game_pause_btn.disabled = false;
        game_reset_btn.disabled = true;
        game_start_btn.disabled = true;
    }
    function game_pause() {
        console.log('Attempting to pause game');
        socket.emit('game_pause', 'defaultgame');
        game_start_btn.innerText = 'Resume game';
        game_start_btn.disabled = false;
        game_reset_btn.disabled = false;
        game_pause_btn.disabled = true;
    }
    function game_reset() {
        console.log('Attempting to reset game');
        socket.emit('game_reset', 'defaultgame');
        game_start_btn.innerText = 'Start game'
        game_pause_btn.disabled = true;
        game_reset_btn.disabled = false;
        game_start_btn.disabled = false;
    }
    $('#username_change').on('click', function () {
        localStorage.setItem('username', username.value);
    });
    $('#username_clear').on('click', function () {
        localStorage.removeItem('username');
        username.value = "";
    });
});