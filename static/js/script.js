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
    let question = document.getElementById('question');

    var local_game_state;
    var local_game_state_html;
    var default_game_state = { 'game_state': 'SETUP', 'players': [], 'time': 300 };

    var timer;
    game_timer = document.getElementById('game_timer');
    reset_game_timer(default_game_state['time']);
    function reset_game_timer(seconds) {
        timer = new easytimer.Timer({
            countdown: true,
            startValues: { seconds: default_game_state['time'] }
        });
        game_timer.innerHTML = timer.getTimeValues().toString();
        timer.addEventListener('secondsUpdated', function (e) {
            game_timer.innerHTML = timer.getTimeValues().toString();
        });
        timer.addEventListener('targetAchieved', function (e) {
            game_timer.innerHTML = 'KABOOM!!';
        });
    }

    function print_game_state_html(game_state) {
        var players = game_state['players'].join('<br>');
        // for (var i = 0; i < game_state['players'].length; i++) {
        //     console.log(i);
        //     console.log(game_state['players'][i]);
        //     players = players + '<br>' + game['players'][i];
        // };
        console.log(players);
        var questions = game_state['questions'].join('<br>');
        console.log(questions);
        var question_html = new Array();
        var i = 0;
        for (const e of game_state['questions']) {
            question_html.push('<br><div id="q' + i + '">' + e + '</div>');
            i++;
        }
        console.log(question_html.join(''));

        return '<div id="game_status" style="width:640px; height:240px;">Game state: ' + game_state['game_state'] + '<br> Players: ' + players + '<br> Questions: ' + question_html + '<br> time left: ' + game_state['time'] + '</div>';
    }

    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('disconnect', function () {
        console.log('Socket disconnected.');
    });
    function foo(g) {

    };
    socket.on('game_state', function (g) {
        console.log('Game state received.')
        local_game_state = g;
        gs = print_game_state_html(g);
        console.log('parsed game state: ' + gs);
        document.getElementById("game_status").innerHTML = print_game_state_html(g);
    });
    socket.on('pause', function (time) {
        reset_game_timer(time);
        console.log('Pausing timer with ' + time + ' seconds left.');
    });

    document.getElementById('question_submit').addEventListener('click', function () {
        console.log('emitting question: ' + question.value);
        if (question.value != "") {
            socket.emit('question', question.value);
        }
    });

    var game_start_btn = document.getElementById('game_start');
    var game_pause_btn = document.getElementById('game_pause');
    var game_reset_btn = document.getElementById('game_reset');
    var get_game_state_btn = document.getElementById('get_game_state');
    var proper_noun_btn = document.getElementById('proper_noun');
    game_start_btn.addEventListener('click', game_start_resume);
    game_pause_btn.addEventListener('click', game_pause);
    game_reset_btn.addEventListener('click', game_reset);
    get_game_state_btn.addEventListener('click', get_game_state);
    proper_noun_btn.addEventListener('click', function () {
        socket.emit('question', "Is it a proper noun?");
    });
    function game_start_resume() {
        console.log('Attempting to start game');
        socket.emit('game_start', 'defaultgame');
        timer.start();
        game_start_btn.innerText = 'Start game';
        game_start_btn.disabled = true;
        game_reset_btn.disabled = true;
        game_pause_btn.disabled = false;
        proper_noun_btn.disabled = false;
    };
    function game_pause() {
        console.log('Attempting to pause game');
        socket.emit('game_pause', 'defaultgame');
        timer.pause();
        game_start_btn.innerText = 'Resume game';
        game_start_btn.disabled = false;
        game_reset_btn.disabled = false;
        game_pause_btn.disabled = true;
        proper_noun_btn.disabled = true;
    };
    function game_reset() {
        console.log('Attempting to reset game');
        socket.emit('game_reset', 'defaultgame');
        // reset_game_timer(default_game_state['time']);
        reset_game_timer(60);
        game_start_btn.innerText = 'Start game';
        game_start_btn.disabled = false;
        game_reset_btn.disabled = false;
        game_pause_btn.disabled = true;
        proper_noun_btn.disabled = true;
    };
    function get_game_state() {
        socket.emit('get_game_state', 'defaultgame');
        console.log('Game state request initiated')
    };
    function parse_game_state(game_state) {
        if (default_game_state['game_state'] == 'STARTED') {
            reset_game_timer(default_game_state);
            game_timer.timer('start');
        };
    };
    // TODO: make this so it puts the most recent question at the top...
    // socket.on('returndata', function (data) {
    //     chat.innerHTML = "<pre>" + data + "</pre>" + chat.innerHTML;
    // });
});