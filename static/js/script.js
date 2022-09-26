$(document).ready(function () {
    // TODO: update all defaultgame references
    // TODO: update all default_game_state to be the local_game_state after
    //       emitting the correct values form server
    // TODO: add separate sockets for each of the game comms
    var socket = io({ autoconnect: true });
    let username = document.getElementById('username');
    let question = document.getElementById('question');

    let game_start_btn = document.getElementById('game_start');
    let game_pause_btn = document.getElementById('game_pause');
    let game_reset_btn = document.getElementById('game_reset');

    // if (localStorage.getItem("username") == null |
    //     localStorage.getItem("username") == "") {
    //     let default_username = 'Not_a_wolf_' + Math.floor(Math.random() * 10000 % 9999);
    //     username.defaultValue = default_username;
    //     localStorage.setItem('username', default_username);
    //     localStorage.setItem('role', 'spectator');
    // } else {
    //     username.defaultValue = localStorage.getItem("username");
    // }
    // var user = username.value;
    var local_game_state = {};
    var default_game_state = { 'game_state': 'SETUP', 'players': [], 'time': 300 };

    var timer = null;
    reset_game_timer(default_game_state['time']);
    function reset_game_timer(seconds) {
        timer = new easytimer.Timer({
            countdown: true,
            startValues: { seconds: default_game_state['time'] }
        });
        $('#game_timer').html(timer.getTimeValues().toString());
        timer.addEventListener('secondsUpdated', function (e) {
            $('#game_timer').html(timer.getTimeValues().toString());
        });
        timer.addEventListener('targetAchieved', function (e) {
            $('#game_timer').html('KABOOM!!');
        });
    }

socket.on('connect', function () {
    console.log('You are like connected and stuff.');
});
socket.on('game_state', function (game_state) {
    local_game_state = game_state;
    console.log(game_state);
});
socket.on('pause', function (time) {
    reset_game_timer(time);
    console.log('Pausing timer with ' + time + ' seconds left.');
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
$('#get_game_state').on('click', get_game_state);
$('#proper_noun').on('click', function () {
    socket.emit('data', "[" + user + "]: Is it a proper noun?")
})
function game_start_resume() {
    console.log('Attempting to start game');
    socket.emit('game_start', 'defaultgame');
    timer.start();
    game_start_btn.innerText = 'Start game';
    game_pause_btn.disabled = false;
    game_reset_btn.disabled = true;
    game_start_btn.disabled = true;
}
function game_pause() {
    console.log('Attempting to pause game');
    socket.emit('game_pause', 'defaultgame');
    timer.pause();
    game_start_btn.innerText = 'Resume game';
    game_start_btn.disabled = false;
    game_reset_btn.disabled = false;
    game_pause_btn.disabled = true;
}
function game_reset() {
    console.log('Attempting to reset game');
    socket.emit('game_reset', 'defaultgame');
    // reset_game_timer(default_game_state['time']);
    reset_game_timer(60);
    game_start_btn.innerText = 'Start game';
    game_pause_btn.disabled = true;
    game_reset_btn.disabled = false;
    game_start_btn.disabled = false;
}
function get_game_state() {
    socket.emit('get_game_state', 'defaultgame');
}
function parse_game_state(game_state) {
    if (default_game_state['game_state'] == 'STARTED') {
        reset_game_timer(default_game_state)
        $('#game_timer').timer('start')
    }

}
// $('#username_change').on('click', function () {
//     if (username.value != "") {
//         localStorage.setItem("username", username.value);
//     } else {
//         alert("Username can not be blank.");
//         console.log("Username blank");
//     }
// });
// $('#username_clear').on('click', function () {
//     localStorage.removeItem('username');
//     username.value = "";
// });
});