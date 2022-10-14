var socket = io.connect({ autoconnect: true });
function hideSidebar() {
    document.getElementById('openSideMenu').checked = false;
}
function answer(id, answer) {
    socket.emit('answer_question', id, answer);
}


function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

ready(function () {
    // Side bar click-to-hide stuff
    var sideIconToggle = document.getElementById('sidebarContainer');
    document.addEventListener('click', function (event) {
        if (!sidebarContainer.contains(event.target))
            hideSidebar();
    });

    // TODO: add separate sockets for each of the game comms
    // TODO: Reload the page with the correct buttons appearing
    // var socket = io.connect({ autoconnect: true });
    var questions = document.getElementById("questions");
    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('disconnect', function () {
        console.log('Socket disconnected.');
    });
    socket.on('game_state', function (g) {
        console.log('Game state received.');
        console.log('local game state before: ' + local_game_state.game_id)
        console.log('Received game state for game id: ' + g.game_id)
        local_game_state = g;
        console.log('local game state after: ' + local_game_state.game_id);
        console.log('local game state after: ' + local_game_state.player);
        console.log('local game state after: ' + local_game_state.am_mayor);
        console.log('local game state after: ' + local_game_state.mayor);
        console.log('questions: ' + g['questions'].join())
        if (g.questions.length > 0) {
            questions.innerHTML = g.questions.join('');
        } else {
            questions.innerHTML = '';
        }
    });
    // TODO: Break this away from using local_game_state or make it so it gets
    //       game state on connect
    socket.on('game_start_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_start_resume();
        }
    });
    socket.on('game_reset_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_reset(game_id);
        }
    });
    socket.on('mayor_error', function (date) {
        if (role === 'mayor') {
            alert(data)
        }
    });
    socket.on('add_question', function (rsp) {
        if (local_game_state.game_id === rsp.game_id) {
            questions.innerHTML = rsp.q + questions.innerHTML
        }
    });

    var local_game_state = {
        'game_state': null,
        'players': [],
        'questions': [],
        'time': 420,
        'game_id': null,
        'role': null,
    }

    var timer;
    game_timer = document.getElementById('game_timer');
    reset_game_timer(local_game_state['time']);
    function reset_game_timer(seconds) {
        timer = new easytimer.Timer({
            countdown: true,
            startValues: { seconds: local_game_state['time'] }
        });
        game_timer.innerHTML = timer.getTimeValues().toString();
        timer.addEventListener('secondsUpdated', function (e) {
            game_timer.innerHTML = timer.getTimeValues().toString();
        });
        timer.addEventListener('targetAchieved', function (e) {
            game_timer.innerHTML = 'KABOOM!!';
        });
    }

    document.getElementById('question_submit').addEventListener('click', function () {
        console.log('emitting question: ' + question.value);
        if (question.value != "") {
            socket.emit('question', question.value);
        }
    });

    questions = document.getElementById('questions');
    var game_start_btn = document.getElementById('game_start');
    var game_reset_btn = document.getElementById('game_reset');
    var get_game_state_btn = document.getElementById('get_game_state');
    var proper_noun_btn = document.getElementById('proper_noun');
    var undo_btn = document.getElementById('undo');
    var make_me_mayor_btn = document.getElementById('make_me_mayor');
    game_start_btn.addEventListener('click', send_start_req);
    game_reset_btn.addEventListener('click', send_reset_req);
    get_game_state_btn.addEventListener('click', get_game_state);
    undo_btn.addEventListener('click', function () {
        socket.emit('undo', local_game_state.game_id)
    })
    make_me_mayor_btn.addEventListener('click', function () {
        socket.emit('make_me_mayor', local_game_state.game_id)
    })
    proper_noun_btn.addEventListener('click', function () {
        socket.emit('question', "Is it a proper noun?");
    });
    function send_start_req() {
        console.log('Attempting to start');
        if (local_game_state.game_id !== '') {
            console.log('Start timer for game: ' + local_game_state.game_id);
            socket.emit('game_start_req', local_game_state.game_id);
        }
    }
    function send_reset_req() {
        if (local_game_state.game_id !== '') {
            console.log('Start timer for game: ' + local_game_state.game_id);
            socket.emit('game_reset_req', local_game_state.game_id);
        }
    }
    function game_start_resume() {
        console.log('Attempting to start game');
        timer.start();
        game_start_btn.disabled = true;
        game_reset_btn.disabled = false;
        proper_noun_btn.hidden = false;
        // undo_btn.hidden = false;
        // answer_btns = document.querySelectorAll('.answer');
        // for (i = 0; i < answer_btns.length; i++) {
        //     answer_btns[i].hidden = false;
        // }
    }
    function game_reset(game_id) {
        // FIXME: Game reset does not remove existing questions from board.
        console.log('Attempting to reset game');
        if (game_id === local_game_state.game_id) {
            socket.emit('game_reset', game_id);
            reset_game_timer(local_game_state.time);
            game_start_btn.disabled = false;
            game_reset_btn.disabled = false;
            proper_noun_btn.hidden = true;
        }
    }
    function get_game_state() {
        socket.emit('get_game_state');
        console.log('Game state request initiated');
    }
    function get_role(game_id) {
        socket.emit('get_role', game_id);
    }
});