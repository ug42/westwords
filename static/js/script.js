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
    // Button variables
    var game_start_btn = document.getElementById('game_start');
    var game_reset_btn = document.getElementById('game_reset');
    var proper_noun_btn = document.getElementById('proper_noun');
    var nominate_mayor_btn = document.getElementById('nominate_mayor');

    // div variables
    var question_div = document.getElementById('question_div');
    var game_state = document.getElementById('game_state');
    var mayor_name = document.getElementById('mayor_name');
    var token_count = document.getElementById('token_count');
    var questions = document.getElementById('questions');
    // Get the button that opens the modal
    var modal = document.getElementById("modal-div");
    var modal_text = document.getElementById('modal-text');
    // Get the <span> element that closes the modal
    var close_modal = document.getElementsByClassName("close")[0];

    document.addEventListener('click', function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
        if (!sidebarContainer.contains(event.target))
            hideSidebar();
    });
    close_modal.onclick = function () {
        modal.style.display = "none";
    }

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
        local_game_state = g;
        if (g.questions.length > 0) {
            questions.innerHTML = g.questions.join('');
            if (local_game_state.am_mayor === true) { unhide_answer_btns(); }
        } else {
            questions.innerHTML = '';
        }

        token_count.innerHTML = "Remaining tokens: " + local_game_state.tokens;
        game_state.innerHTML = 'Game state: ' + local_game_state.game_state;
        mayor_name.innerHTML = 'Mayor: ' + local_game_state.mayor;

        if (local_game_state.mayor !== 'No Mayor yet elected') {
            nominate_mayor_btn.hidden = true;
        }
        if (local_game_state.am_mayor === true) {
            nominate_mayor_btn.hidden = true;
            proper_noun_btn.hidden = true;
            // undo_btn.hidden = false;
            question_div.hidden = true;
            unhide_answer_btns();
        } else {
            // question_div.hidden = false;
            proper_noun_btn.hidden = false;
            // undo_btn.hidden = true;
        }
    });
    socket.on('game_start_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_start();
        }
    });
    socket.on('game_reset_rsp', function (game_id) {
        if (local_game_state.game_id === game_id) {
            game_reset(game_id);
        }
    });
    socket.on('mayor_error', function (data) {
        if (local_game_state.am_mayor === true) {
            modal_text.innerHTML = data;
            modal.style.display = "block";
        }
    });
    socket.on('admin_error', function (data) {
        if (local_game_state.am_admin === true) {
            modal_text.innerHTML = data;
            modal.style.display = "block";
        }
    });
    socket.on('add_question', function (rsp) {
        if (local_game_state.game_id === rsp.game_id) {
            questions.innerHTML = rsp.q + questions.innerHTML
            if (local_game_state.am_mayor) { unhide_answer_btns(); }
        }
    });
    socket.on('force_refresh', function (rsp) {
        if (local_game_state.game_id === rsp) {
            console.log('Force refresh for ' + local_game_state.game_id);
            get_game_state();
        }
    })

    var local_game_state = {
        'game_state': null,
        'players': [],
        'questions': [],
        'time': 420,
        'game_id': null,
        'role': null,
        'am_mayor': null,
        'am_admin': null,
        'tokens': null,
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

    function unhide_answer_btns() {
        answer_btns = document.querySelectorAll('.answer');
        for (i = 0; i < answer_btns.length; i++) {
            answer_btns[i].hidden = false;
        }
    }

    var question = document.getElementById('question');
    question.addEventListener('keypress', function (event) {
        if (event.key === "Enter") {
            console.log('emitting question: ' + question.value);
            if (question.value != "") {
                socket.emit('question', question.value);
                question.value = "";
            }
        }
    });
    document.getElementById('question_submit').addEventListener('click', function () {
        console.log('emitting question: ' + question.value);
        if (question.value != "") {
            socket.emit('question', question.value);
            question.value = "";
        }
    });

    game_start_btn.addEventListener('click', send_start_req);
    game_reset_btn.addEventListener('click', send_reset_req);
    if (document.getElementById('undo') !== null) {
        let undo_btn = document.getElementById('undo');
        undo_btn.addEventListener('click', function () {
            socket.emit('undo', local_game_state.game_id)
        })
    }
    nominate_mayor_btn.addEventListener('click', function () {
        socket.emit('nominate_mayor', local_game_state.game_id)
    })
    if (document.getElementById('get_game_state')) {
        let get_game_state_btn = document.getElementById('get_game_state');
        get_game_state_btn.addEventListener('click', get_game_state);
    }
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
    function game_start() {
        console.log('Attempting to start game');
        timer.start();
        // game_start_btn.hidden = true;
        // game_reset_btn.hidden = false;

        // if (local_game_state.am_mayor === true) {
        //     unhide_answer_btns();
        //     question_div.hidden = true;
        //     proper_noun_btn.hidden = true;
        // } else {
        //     question_div.hidden = false;
        //     proper_noun_btn.hidden = false;
        // }

    }
    function game_reset(game_id) {
        // FIXME: Game reset does not remove existing questions from board.
        console.log('Attempting to reset game');
        if (game_id === local_game_state.game_id) {
            socket.emit('game_reset', game_id);
            reset_game_timer(local_game_state.time);
            game_start_btn.hidden = false;
            game_reset_btn.hidden = true;
            proper_noun_btn.hidden = true;
        }
    }
    function get_game_state() {
        socket.emit('get_game_state');
        console.log('Game state refresh requested');
    }
    function get_role(game_id) {
        socket.emit('get_role', game_id);
    }
});