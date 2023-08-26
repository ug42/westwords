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
    if (JSON.stringify(local_game_state) === '{}') {
        timestamp = 0;
    } else {
        timestamp = local_game_state.update_timestamp;
    }
    socket.emit('get_game_state', game_id, timestamp, (response) => {
        if (response.status === 'OK') {
            refresh_game_state(response.game_state);
        } else if (response.status === 'NO_UPDATE') {
            console.log('Game state unchanged.')
        } else {
            console.info('Failed to retrieve game state.');
        }
    });
}
function close_dialog() {
    let dialog = document.querySelector('dialog');
    dialog.close()
}
function answer(game_id, id, answer) {
    socket.emit('answer_question', game_id, id, answer);
}
function send_word(game_id, word) {
    socket.emit('set_word', game_id, word);
    let dialog = document.querySelector('dialog');
    dialog.close()
}
function ack_reveal() {
    close_dialog();
    socket.emit('acknowledge_revealed_info', local_game_state.game_id);
}
function ask_question(game_id, question) {
    socket.emit('question', game_id, question);
}
function undo_answer(game_id) {
    socket.emit('undo', game_id);
    close_dialog()
}
function start_vote(game_id) {
    socket.emit('start_vote', game_id)
    close_dialog()
}
function send_start_req() {
    socket.emit('game_start', local_game_state.game_id);
}
function send_reset_req() {
    socket.emit('game_reset', local_game_state.game_id);
}
function set_player_target(game_id, target) {
    socket.emit('set_player_target', game_id, target)
}
function set_doppelganger_target(game_id, target) {
    socket.emit('set_player_target', game_id, target)
}
function vote_player(game_id, candidate) {
    socket.emit('vote', game_id, candidate)
}
// socket.on('game_state', function (state) {
//     refresh_game_state(state);
// });

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
    // timer.start();
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = true;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = false;
    let join_game_btn = document.getElementById('join_game');
    join_game_btn.hidden = true;
    let mayor_display = document.getElementById('mayor_display');
    mayor_display.hidden = false;
    let spectate_btn = document.getElementById('spectate');
    spectate_btn.hidden = true;
}

function game_setup_buttons() {
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = false;
    let game_reset_btn = document.getElementById('game_reset');
    game_reset_btn.hidden = true;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = true;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = true;
    let mayor_display = document.getElementById('mayor_display');
    mayor_display.hidden = true;
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

function correct_for_server_time_skew(timestamp_ms, server_timestamp_ms) {
    local_time_ms = Date.now()
    let time_skew = timestamp_ms - server_timestamp_ms
    // Since we are subtracting server time from local timestamp, we add
    return timestamp_ms + time_skew
}

function format_time(timer_ms) {
    // Time calculations for days, hours, minutes and seconds
    function printf_02d(number) {
        return (number < 10 ? '0' : '') + number
    }
    var minutes = printf_02d(
        Math.floor((timer_ms % (1000 * 60 * 60)) / (1000 * 60)));
    var seconds = printf_02d(
        Math.floor((timer_ms % (1000 * 60)) / 1000));

    // Retun MM:SS string
    return minutes + ":" + seconds;
}

function start_timer(end_timestamp_ms) {
    // Set the date we're counting down to
    let game_timer = document.getElementById('game_timer');

    if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS' &&
        typeof refresh_timer === 'undefined') {
        // Update the count down every 1 second
        var refresh_timer = setInterval(function () {
            let now = Date.now();
            let remaining_ms = end_timestamp_ms - now

            // If the count down is over, write some text 
            if (remaining_ms < 0) {
                clearInterval(refresh_timer);
                game_timer.innerHTML = "00:00";
                if (local_game_state.player_is_mayor) {
                    start_vote(local_game_state.game_id)
                }
            }
            game_timer.innerHTML = format_time(remaining_ms);
        }, 1000);

    }
}

(function () {
    window.onpageshow = function (event) {
        if (event.persisted) {
            window.location.reload();
        }
    };
})();

function refresh_game_state(g) {
    console.log('Attempting to refresh game state')
    local_game_state = g;
    close_dialog()

    // TODO: Remove this or check to see if game_state is available
    let game_state = document.getElementById('game_state');
    if (game_state !== null) {
        game_state.innerHTML = local_game_state.game_state;
    }

    let game_timer = document.getElementById('game_timer');
    game_timer.innerHTML = format_time(local_game_state.timer * 1000);

    let mayor_tokens = document.getElementById('mayor_tokens');
    mayor_tokens.innerHTML = parse_tokens(local_game_state.tokens);

    let players = document.getElementById('players');
    players.innerHTML = format_players(local_game_state);

    let questions_div = document.getElementById('questions_div');
    questions_div.innerHTML = local_game_state.question_html;

    let question_input = document.getElementById('question_input');
    question_input.hidden = true;
    let proper_noun_btn = document.getElementById('proper_noun');
    proper_noun_btn.hidden = true;
    let breadbox_btn = document.getElementById('breadbox');
    breadbox_btn.hidden = true;
    let dialog_box = document.getElementById('dialog-box');
    dialog_box.hidden = true;
    let controls = document.getElementById('controls');
    controls.hidden = false;
    let dialog = document.querySelector('dialog');

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

    let title_bar_role = document.getElementById('title-bar-role');
    if (local_game_state.role !== 'None') {
        let html = 'Role: ' + local_game_state.role;
        if (local_game_state.player_is_mayor) {
            html += ' [Mayor]'
        }
        title_bar_role.innerHTML = html
    } else {
        title_bar_role.innerHTML = 'Waiting...';
    }

    if (local_game_state.game_state === 'NIGHT_PHASE_DOPPELGANGER' ||
        local_game_state.game_state === 'NIGHT_PHASE_TARGETTING') {
        socket.emit('get_night_action_page', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                dialog.innerHTML = response.night_action_html;
                dialog.showModal();
            }
        });
    }
    if (local_game_state.game_state === 'NIGHT_PHASE_REVEAL') {
        socket.emit('get_player_revealed_information', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                dialog.innerHTML = response.reveal_html;
                dialog.showModal();
            }
        });
    }
    if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS') {
        start_timer(local_game_state.end_timestamp_ms, local_game_state.timer)

        if (!local_game_state.spectating && !local_game_state.player_is_mayor) {
            question_input.hidden = false;
            proper_noun_btn.hidden = false;
            breadbox_btn.hidden = false;
        }
    }
    if (local_game_state.game_state === 'VOTING') {
        socket.emit('get_voting_page', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                dialog_box.innerHTML = response.voting_html;
                dialog_box.hidden = false;
                controls.hidden = true;
            }
        });
    }
    if (local_game_state.game_state === 'FINISHED') {
        socket.emit('get_results', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                dialog_box.innerHTML = response.results_html;
                dialog_box.hidden = false;
                controls.hidden = true;
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
            let dialog = document.querySelector('dialog');
            let html = '<div class="mdl-dialog__content">'
            html += '<p>Last token played, Undo or Move to vote</p>'
            html += '<p><button onclick="undo_answer(\''
            html += local_game_state.game_id
            html += '\')" class="mdl-button">Undo last answer</button></p>'
            html += '<p><button onclick="start_vote(\''
            html += local_game_state.game_id
            html += '\')" class="mdl-button">Start Vote</button></p>'
            html += '<p><button type="button" class="mdl-button close" '
            html += 'onclick="close_dialog()">Close</button></p></div>'
            dialog.innerHTML = html
            dialog.showModal();
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

function ready(fn) {
    if (document.readyState !== 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}
ready(function () {

    var dialog = document.querySelector('dialog');
    if (!dialog.showModal) {
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
    });
    socket.on('user_info', function (message) {
        snackbarContainer.MaterialSnackbar.showSnackbar({ message: message });
    });


    socket.on('mayor_error', function (data) {
        if (local_game_state.player_is_mayor === true) {
            let dialog = document.querySelector('dialog');
            html = data;
            html += '<br><button type="button" class="mdl-button close"';
            html += ' onclick="close_dialog()">OK</button>';
            dialog.innerHTML = html;

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
    socket.on('game_state_update', function (data) {
        if (local_game_state.update_timestamp !== data.timestamp) {
            get_game_state(local_game_state.game_id);
        }
    })

    var question = document.getElementById('question');
    if (question !== null) {
        question.addEventListener('keypress', function (event) {
            if (event.key === "Enter") {
                if (question.value != "") {
                    socket.emit('question', local_game_state.game_id, question.value);
                    question.value = "";
                }
            }
        });
        document.getElementById('question_submit').addEventListener('click', function () {
            if (question.value != "") {
                socket.emit('question', local_game_state.game_id, question.value);
                question.value = "";
            }
        });
    }

});