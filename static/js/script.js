// TODO: add separate sockets for each of the game comms
// TODO: Reload the page with the correct buttons appearing
// TODO: Get the questions to show up with answers for other people after being answered
// TODO: Fix it so the mayor error and admin error are closeable
// TODO: Update on-screen role info on game state change
// TODO: Spectators see no player data

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
    console.log('Attempting to answer question ' + id)
    socket.emit('answer_question', game_id, id, answer);
}
function send_word(game_id, word) {
    socket.emit('set_word', game_id, word);
    let dialog = document.querySelector('dialog');
    dialog.close()
}
function ack_reveal() {
    console.log('Attempting to ack the info');
    close_dialog();
    socket.emit('acknowledge_revealed_info', local_game_state.game_id);
}
function ask_question(game_id, question) {
    socket.emit('question', game_id, question);
}
function undo_answer(game_id) {
    socket.emit('undo', game_id);
}
function start_vote(game_id) {
    console.log('Attempting to start vote.')
    socket.emit('start_vote', game_id)
}
function send_start_req() {
    console.log('Attempting to start');
    console.log('Start timer for game: ' + local_game_state.game_id);
    socket.emit('game_start', local_game_state.game_id);
}
function send_reset_eq() {
    console.log('Start timer for game: ' + local_game_state.game_id);
    socket.emit('game_reset', local_game_state.game_id);
}
function vote_player(game_id, candidate) {
    console.log('trying to vote for ' + candidate);
    socket.emit('vote', game_id, candidate)
}
socket.on('game_state', function (state) {
    console.log('Got a socket connection for game_state updates. Updating..')
    refresh_game_state(state);
});

function format_players(local_game_state) {
    let html = '';
    for (const player in local_game_state.players) {
        html += '<div>' + player
        if (player === local_game_state.admin) {
            html = '<b>' + html + '</b>';
        }
        if (player === local_game_state.mayor) {
            html += ' (Mayor)';
        }
        html += parse_tokens(local_game_state.players[player])
        html += '</div>';
    }
    for (let i = 0; i < local_game_state.spectators.length; i++) {
        html += '<div>' + local_game_state.spectators[i] 
        html += ' (Spectator) </div>';
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
    // console.log('Attempting to start game');
    // timer.start();
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = true;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = false;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = false;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = false;
    let join_game_btn = document.getElementById('join_game');
    join_game_btn.hidden = true;
    let spectate_btn = document.getElementById('spectate');
    spectate_btn.hidden = true;
}

function game_setup_buttons() {
    // reset_game_timer(local_game_state.time);
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = false;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = true;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = true;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = true;
    let mayor_controls = document.getElementById('mayor_controls');
    mayor_controls.hidden = true;
    let admin_controls = document.getElementById('admin_controls');
    admin_controls.hidden = true;
    let join_game_btn = document.getElementById('join_game');
    let spectate_btn = document.getElementById('spectate');
    if (local_game_state.spectating === true) {   
        // If we're already spectating, hide the spectating button, show the
        // join button
        join_game_btn.hidden = false;
        spectate_btn.hidden = true;
    } else {
        // Otherwise, reverse and show the spectate button.
        join_game_btn.hidden = true;
        spectate_btn.hidden = false;
    }
}

function get_time_skew(server_timestamp) {
    let time_skew = Date.now() - server_timestamp
    return time_skew
}

function start_timer(timestamp) {

}

(function () {
	window.onpageshow = function(event) {
		if (event.persisted) {
			window.location.reload();
		}
	};
})();

function refresh_game_state(g) {
    console.log('Attempting to refresh game state')
    local_game_state = g;

    // TODO: Remove this or check to see if game_state is available
    let game_state = document.getElementById('game_state');
    if (game_state !== null) {
        game_state.innerHTML = local_game_state.game_state;
    }

    let mayor_tokens = document.getElementById('mayor_tokens');
    mayor_tokens.innerHTML = parse_tokens(local_game_state.tokens);

    let players = document.getElementById('players');
    players.innerHTML = format_players(local_game_state)

    let questions_div = document.getElementById('questions_div');
    questions_div.innerHTML = local_game_state.question_html;

    let nominate_for_mayor_btn = document.getElementById('nominate_for_mayor');
    if (local_game_state.mayor !== null) {
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

    if (local_game_state.game_state === 'NIGHT_PHASE_REVEAL') {
        socket.emit('get_player_revealed_information', local_game_state.game_id, (response) => {
            let dialog = document.querySelector('dialog');
            if (response.status === 'OK') {
                dialog.innerHTML = response.reveal_html;
                dialog.showModal();
            }
        });
    }
    if (local_game_state.game_state === 'VOTING') {
        socket.emit('get_voting_page', local_game_state.game_id, (response) => {
            let dialog = document.querySelector('dialog');
            console.table(response)
            if (response.status === 'OK') {
                dialog.innerHTML = response.voting_html;
                dialog.showModal();
            }
        });
    }
    if (local_game_state.player_is_admin) {
        let admin_controls = document.getElementById('admin_controls');
        admin_controls.hidden = false;
    }
    if (local_game_state.player_is_mayor) {
        let finish_btn = document.getElementById('finish');
        let mayor_controls = document.getElementById('mayor_controls');
        if (local_game_state.game_state === 'AWAITING_VOTE') {
            mayor_controls.hidden = false;
            finish_btn.hidden = false;
        }
        if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS') {
            mayor_controls.hidden = false;
            finish_btn.hidden = true;
        }
        if (local_game_state.game_state === 'NIGHT_PHASE_WORD_CHOICE') {
            socket.emit('get_words', local_game_state.game_id, (response) => {
                let dialog = document.querySelector('dialog');
                if (response.status === 'OK') {
                    dialog.innerHTML = response.word_html;
                    dialog.showModal();
                }
            });
        }
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
    var dialog = document.querySelector('dialog');
    if (! dialog.showModal) {
      dialogPolyfill.registerDialog(dialog);
    }
    var snackbarContainer = document.querySelector('#demo-toast-example');
    dialog.showModal();
    dialog.close();

    socket.on('connect', function () {
        console.log('You are like connected and stuff.');
    });
    socket.on('disconnect', function (data) {
        console.log('Socket disconnected.');
        console.log(data);
    });
    socket.on('user_info', function (message) {
        snackbarContainer.MaterialSnackbar.showSnackbar({ message: message });
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

});