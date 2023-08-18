// TODO: add separate sockets for each of the game comms
// TODO: Reload the page with the correct buttons appearing
var socket = io.connect({ autoconnect: true });
var local_game_state = {};
var local_time_skew = 0;
function get_game_state(game_id) {
    console.log('Game state refresh requested');
    socket.emit('get_game_state', game_id);
}
function close_dialog() {
    let dialog = document.querySelector('dialog');
    dialog.close()
}
function answer(game_id, id, answer) {
    socket.emit('answer_question', game_id, id, answer);
}
function sendWord(game_id, word) {
    socket.emit('set_word', game_id, word);
    let dialog = document.querySelector('dialog');
    dialog.close()
}
function ackReveal() {
    console.log('Attempting to ack the info');
    close_dialog();
    socket.emit('acknowledge_revealed_info', local_game_state.game_id);
}
function askQuestion(game_id, question) {
    socket.emit('question', game_id, question);
}
function undoAnswer(game_id) {
    socket.emit('undo', game_id);
}
function send_start_req() {
    console.log('Attempting to start');
    console.log('Start timer for game: ' + local_game_state.game_id);
    socket.emit('game_start', local_game_state.game_id);
}
function send_reset_req() {
    console.log('Start timer for game: ' + local_game_state.game_id);
    socket.emit('game_reset', local_game_state.game_id);
}
socket.on('game_state', function(state) {
    local_game_state = state;
    refresh_game_state(local_game_state);
});

function format_players(players) {
    let html = '';
    for (const player in players) {
        html += '<div>' + player
        html += parse_tokens(players.player)
        if (player === local_game_state.player_is_mayor) {
            html += ' (Mayor)';
        }
        if (player === local_game_state.player_is_admin) {
            html += ' [admin]';
        }
        html += '</div>';
    }
    return html
}
function parse_tokens(tokens) {
    let html = '<div style="display: inline;">';
    if (typeof tokens === 'undefined') {
        return '';
    }
    if (typeof tokens.yesno !== 'undefined' && tokens.yesno > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Yes/No" data-badge="';
        html += tokens.yesno;
        html += '">check_circle</div>';
    }
    if (typeof tokens.yes === 'number' && tokens.yes > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Yes" data-badge="';
        html += tokens.yes;
        html += '">check_circle</div>';
    }
    if (typeof tokens.no === 'number' && tokens.no > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="No" data-badge="';
        html += tokens.no;
        html += '">cancel</div>';
    }
    if (typeof tokens.maybe === 'number' && tokens.maybe > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Maybe" data-badge="';
        html += tokens.maybe;
        html += '">help</div>';
    }
    if (typeof tokens.so_far === 'number' && tokens.so_far > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Very far off!">delete_forever</div>';
    }
    if (typeof tokens.so_close === 'number' && tokens.so_close > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="So close!">radar</div>';
    }
    if (typeof tokens.correct === 'number' && tokens.correct > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Correct!">star</div>';
    }
    if (typeof tokens.laramie === 'number' && tokens.laramie > 0) {
        html += '<div class="material-icons mdl-badge mdl-badge--overlap" title="Laramie?">trolley</div>';
    }
    html += "</div>";

    return html;
}

function game_started_buttons() {
    console.log('Attempting to start game');
    // timer.start();
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = true;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = false;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = false;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = false;
    if (local_game_state.player_is_mayor) {
        let mayor_controls = document.getElementById('controls');
        mayor_controls.hidden = false;
    }
}

function game_setup_buttons() {
    console.log('Attempting to reset game');
    // reset_game_timer(local_game_state.time);
    let questions_div = document.getElementById('questions_div');
    questions_div.innerHTML = '';
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = false;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = true;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = true;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = true;
    // let mayor_controls = document.getElementById('controls');
    // mayor_controls.hidden = true;
}

function get_time_skew(server_timestamp) {
    let time_skew = Date.now() - server_timestamp
    return time_skew
}

function start_timer(timestamp) {

}

function refresh_game_state(g) {
    local_game_state = g;
    console.table(local_game_state)
    console.log('Refreshing game state')
    let proper_noun_btn = document.getElementById('proper_noun');
    
    // TODO: Remove this or check to see if game_state is available
    let game_state = document.getElementById('game_state');
    let mayor_tokens = document.getElementById('mayor_tokens');
    let players = document.getElementById('players');
    mayor_tokens.innerHTML = parse_tokens(local_game_state.tokens);
    game_state.innerHTML = local_game_state.game_state;
    players.innerHTML = format_players(local_game_state.players)

    let nominate_for_mayor_btn = document.getElementById('nominate_for_mayor');
    if (local_game_state.mayor !== 'No Mayor yet elected') {
        nominate_for_mayor_btn.hidden = true;
    } else {
        nominate_for_mayor_btn.hidden = false;
        nominate_for_mayor_btn.addEventListener('click', function () {
            socket.emit('nominate_for_mayor', local_game_state.game_id)
        });
    }
    if (local_game_state.game_state === 'SETUP') {
        game_setup_buttons();
    } else {
        game_started_buttons();
    }
    if (local_game_state.game_state === 'NIGHT_PHASE_WORD_CHOICE' && local_game_state.player_is_mayor) {
        socket.emit('get_words', local_game_state.game_id, (response) => {
            let dialog = document.querySelector('dialog');
            if (response.status === 'OK') {
                dialog.innerHTML = response.word_html;
                dialog.showModal();
            }
        });
    }
    if (local_game_state.game_state === 'NIGHT_PHASE_REVEAL') {
        socket.emit('get_player_revealed_information', local_game_state.game_id, (response) => {
            let dialog = document.querySelector('dialog');
            if (response.status === 'OK') {
                dialog.innerHTML = response.reveal_html;
                dialog.showModal();
            }
        });
    }   
};

// function timer_update(state, players, $section) {
//     var $clock, clock_text, millis_left, minutes_left, now, seconds, seconds_left, timeout;
//     $clock = $section.find('.clock');
//     now = netgames.to_server_timestamp(Date.now());
//     millis_left = Math.max(0, state.deadline - now);
//     seconds_left = Math.floor(millis_left / 1000);
//     minutes_left = Math.floor(seconds_left / 60);
//     seconds = ('0' + (seconds_left - minutes_left * 60)).slice(-2);
//     clock_text = minutes_left + ":" + seconds;
//     if (millis_left <= 10 * 1000) {
//       $clock.text(seconds);
//     } else {
//       $clock.text(clock_text);
//     }
//     $('#cheatsheet-screen .clock').text(clock_text);
//     $clock.toggleClass('large', millis_left <= 10 * 1000);
//     timeout = millis_left > 0 ? millis_left % 1000 : 1000;
//     return clock_timeout = setTimeout(function() {
//       return netgames.refresh(state, players);
//     }, timeout);
//   }
// },

function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}
ready(function () {
    // var dialog = document.querySelector('dialog');
    // if (! dialog.showModal) {
    //   dialogPolyfill.registerDialog(dialog);
    // }
    var snackbarContainer = document.querySelector('#demo-toast-example');
    // dialog.showModal();
    // dialog.close();

    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('disconnect', function (data) {
        console.log('Socket disconnected.');
        console.log(data);
    });
    // socket.on('game_state', function (g) {
    socket.on('game_start_rsp', game_start);
    socket.on('game_reset_rsp', game_reset);
    socket.on('user_info', function(message) {
        snackbarContainer.MaterialSnackbar.showSnackbar({message: message});
    });

        
    socket.on('mayor_error', function (data) {
        if (local_game_state.player_is_mayor === true) {
            let dialog = document.querySelector('dialog');
            dialog.innerHTML = data;
            
            dialog.showModal();
        }
    });
    socket.on('admin_error', function (data) {
        if (local_game_state.player_is_admin === true) {
            let dialog = document.querySelector('dialog');
            dialog.innerHTML = data;
            dialog.showModal();
        }
    });
    socket.on('new_question', function (rsp) {
        console.log('Checkpoint 3');
        if (local_game_state.game_id === rsp.game_id) {
            socket.emit('get_question',
                rsp.game_id, rsp.question_id,
                (response) => {
                    if (response.status === 'OK') {
                        let questions_div = document.getElementById('questions_div');
                        questions_div.innerHTML = response.question + questions_div.innerHTML;
                    }
                });
            console.log('Checkpoint 3.5');
        }
    });

    // // var timer;
    // // game_timer = document.getElementById('game_timer');
    // reset_game_timer(local_game_state.time);
    // function reset_game_timer(seconds) {
    //     timer = new easytimer.Timer({
    //         countdown: true,
    //         startValues: { seconds: seconds }
    //     });
    //     game_timer.innerHTML = timer.getTimeValues().toString();
    //     timer.addEventListener('secondsUpdated', function (e) {
    //         game_timer.innerHTML = timer.getTimeValues().toString();
    //     });
    //     timer.addEventListener('targetAchieved', function (e) {
    //         game_timer.innerHTML = 'KABOOM!!';
    //     });
    // }

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

});