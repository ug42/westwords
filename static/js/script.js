function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

ready(function () {
    // Side bar click-to-hide stuff
    function hideSidebar() {
        document.getElementById('openSideMenu').checked = false;
    }
    var sideIconToggle = document.getElementById('sidebarContainer');
    document.addEventListener('click', function (event) {
        if (!sidebarContainer.contains(event.target))
            hideSidebar();
    });
    // TODO: Factor out jquery
    // TODO: update all defaultgame references
    // TODO: update all default_game_state to be the local_game_state after
    //       emitting the correct values form server
    // TODO: add separate sockets for each of the game comms
    var socket = io.connect({ autoconnect: true });
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
        console.log('local game state after: ' + local_game_state.game_id)
        // gs = get_questions_html(local_game_state);
        // questions.innerHTML = gs;
        console.log('questions: ' + g['questions'].join())
        if (g.questions.length > 0){
            questions.innerHTML = g.questions.join('');
        }
    });
    // TODO: Break this away from using local_game_state or make it so it gets
    //       game state on connect
    socket.on('game_start_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_start_resume();
        };
    });
    socket.on('game_pause_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_pause();
        };
    });
    socket.on('game_reset_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_reset();
        };
    });
    socket.on('mayor_error', function (date) {
        if (role === 'mayor') {
            alert(data)
        }
    })
    socket.on('add_question', function(rsp) {
        if (local_game_state.game_id === rsp.game_id) {
            questions.innerHTML = rsp.q + questions.innerHTML      };
    })

    var local_game_state = {
        'game_state': null,
        'players': [],
        'questions': [],
        'time': 420,
        'game_id': null
    };

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

    var game_start_btn = document.getElementById('game_start');
    // var game_pause_btn = document.getElementById('game_pause');
    var game_reset_btn = document.getElementById('game_reset');
    var get_game_state_btn = document.getElementById('get_game_state');
    var proper_noun_btn = document.getElementById('proper_noun');
    game_start_btn.addEventListener('click', send_start_req);
    // game_pause_btn.addEventListener('click', send_pause_req);
    game_reset_btn.addEventListener('click', send_reset_req);
    get_game_state_btn.addEventListener('click', get_game_state);
    proper_noun_btn.addEventListener('click', function () {
        socket.emit('question', "Is it a proper noun?");
    });
    function send_start_req() {
        console.log('Attempting to start');
        if (local_game_state['game_id'] !== '') {
            console.log('Start timer for game: ' + local_game_state['game_id']);
            socket.emit('game_start_req', local_game_state['game_id']);
        };
    };
    // function send_pause_req() {
    //     if (local_game_state['game_id'] !== '') {
    //         console.log('Start timer for game: ' + local_game_state['game_id']);
    //         socket.emit('game_pause_req', local_game_state['game_id']);
    //     };
    // };
    function send_reset_req() {
        if (local_game_state['game_id'] !== '') {
            console.log('Start timer for game: ' + local_game_state['game_id']);
            socket.emit('game_reset_req', local_game_state['game_id']);
        };
    };
    function game_start_resume() {
        console.log('Attempting to start game');
        timer.start();
        // game_start_btn.innerText = 'Pause game';
        game_start_btn.disabled = true;
        game_reset_btn.disabled = false;
        // game_pause_btn.disabled = false;
        proper_noun_btn.disabled = false;
    };
    // function game_pause() {
    //     console.log('Attempting to pause game');
    //     timer.pause();
    //     game_start_btn.innerText = 'Resume game';
    //     game_start_btn.disabled = false;
    //     game_reset_btn.disabled = false;
    //     game_pause_btn.disabled = true;
    //     proper_noun_btn.disabled = true;
    // };
    // FIXME: socket disconnect on execution of game_reset. Boooo
    function game_reset() {
        console.log('Attempting to reset game');
        socket.emit('game_reset', 'defaultgame');
        reset_game_timer(local_game_state.time);
        // game_start_btn.innerText = 'Start game';
        game_start_btn.disabled = false;
        game_reset_btn.disabled = false;
        // game_pause_btn.disabled = true;
        proper_noun_btn.disabled = true;
    };
    function get_game_state() {
        socket.emit('get_game_state');
        console.log('Game state request initiated')
    };
});