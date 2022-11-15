// TODO: add separate sockets for each of the game comms
// TODO: Reload the page with the correct buttons appearing
var socket = io.connect({ autoconnect: true });
var local_game_state = {
    'game_state': null,
    'players': [],
    'questions': [],
    'time': 0,
    'game_id': null,
    'role': null,
    'am_mayor': null,
    'am_admin': null,
    'tokens': null,
};

function answer(game_id, id, answer) {
    socket.emit('answer_question', game_id, id, answer);
}
function sendWord(game_id, word) {
    socket.emit('set_word', game_id, word);
}
function undoAnswer(game_id) {
    socket.emit('undo', game_id);
}
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
function get_game_state(game_id) {
    socket.emit('get_game_state', game_id);
    console.log('Game state refresh requested');
}

function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

ready(function () {
    // Button variables
    var proper_noun_btn = document.getElementById('proper_noun');
    var nominate_for_mayor_btn = document.getElementById('nominate_for_mayor');

    // div variables
    var question_div = document.getElementById('question_div');
    // var game_state = document.getElementById('game_state');
    // var mayor_name = document.getElementById('mayor_name');
    // var token_count = document.getElementById('token_count');

    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('disconnect', function () {
        console.log('Socket disconnected.');
    });
    socket.on('game_state', function (g) {
        local_game_state = g;
        // token_count.innerHTML = "Remaining tokens: " + local_game_state.tokens;
        game_state.innerHTML = 'Game state: ' + local_game_state.game_state;
        mayor_name.innerHTML = 'Mayor: ' + local_game_state.mayor;

        if (local_game_state.mayor !== 'No Mayor yet elected') {
            nominate_for_mayor_btn.hidden = true;
        }
        // if (local_game_state.am_mayor === true) {
        //     nominate_for_mayor_btn.hidden = true;
        //     proper_noun_btn.hidden = true;
        // } else {
        //     proper_noun_btn.hidden = false;
        // }
    });
    socket.on('game_start_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_start();
        }
    });
    socket.on('game_reset_rsp', function () {
        if (local_game_state.game_id === game_id) {
            game_reset(game_id);
        }
    });
    // socket.on('mayor_error', function (data) {
    //     // if (local_game_state.am_mayor === true) {
    //     //     modal_text.innerHTML = data;
    //     //     modal.style.display = "block";
    //     // }
    // });
    // socket.on('admin_error', function (data) {
    //     // if (local_game_state.am_admin === true) {
    //     //     modal_text.innerHTML = data;
    //     //     modal.style.display = "block";
    //     // }
    // });
    socket.on('new_question', function (rsp) {
        console.log('Checkpoint 3');
        if (local_game_state.game_id === rsp.game_id) {
           socket.emit('get_question_req', rsp.game_id, rsp.question_id);            
           console.log('Checkpoint 3.5');
        }
    });
    socket.on('get_question_rsp'), function(rsp) {
        console.log('Checkpoint 4');
        if (local_game_state.game_id === rsp.game_id) {
            question_div.innerHTML = rsp.question + question_div.innerHTML;
        }
    }
    socket.on('force_refresh', function (rsp) {
        if (local_game_state.game_id === rsp) {
            console.log('Force refresh for ' + local_game_state.game_id);
            get_game_state();
        }
    })

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

    var question = document.getElementById('question');
    question.addEventListener('keypress', function (event) {
        if (event.key === "Enter") {
            console.log('emitting question: ' + question.value);
            if (question.value != "") {
                socket.emit('question', local_game_state.game_id, question.value);
                question.value = "";
            }
        }
    });
    document.getElementById('question_submit').addEventListener('click', function () {
        console.log('emitting question: ' + question.value);
        if (question.value != "") {
            socket.emit('question', local_game_state.game_id, question.value);
            question.value = "";
        }
    });

    if (document.getElementById('undo') !== null) {
        let undo_btn = document.getElementById('undo');
        undo_btn.addEventListener('click', function () {
            socket.emit('undo', local_game_state.game_id)
        })
    }
    nominate_for_mayor_btn.addEventListener('click', function () {
        socket.emit('nominate_for_mayor', local_game_state.game_id)
    })
    // if (document.getElementById('get_game_state')) {
    //     let get_game_state_btn = document.getElementById('get_game_state');
    //     get_game_state_btn.addEventListener('click', get_game_state);
    // }
    proper_noun_btn.addEventListener('click', function () {
        socket.emit('question', local_game_state.game_id, "Is it a proper noun?");
    });


    function game_start() {
        console.log('Attempting to start game');
        timer.start();
    }
    function game_reset() {
        // FIXME: Game reset does not remove existing questions from board.
        console.log('Attempting to reset game');
        reset_game_timer(local_game_state.time);
        game_start_btn.hidden = false;
        game_reset_btn.hidden = true;
        proper_noun_btn.hidden = true;
    }
    function get_role(game_id) {
        socket.emit('get_role', game_id);
    }
});