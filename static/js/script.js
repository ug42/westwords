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
            console.log('Game state unchanged.');
        } else {
            console.info('Failed to retrieve game state.');
        }
    });
}
function close_dialog() {
    let dialog = document.querySelector('dialog');
    dialog.close();
}
function set_timer(game_id, timer_seconds) {
    socket.emit('set_timer', game_id, timer_seconds);
}
function answer(game_id, id, answer) {
    socket.emit('answer_question', game_id, id, answer);
}
function boot_player(game_id, player_sid) {
    console.log('Attempting to boot player: ' + game_id + ': ' + player_sid)
    socket.emit('boot_player', game_id, player_sid)
}
function delete_question(game_id, question_id) {
    socket.emit('delete_question', game_id, question_id);
}
function send_word(game_id, word) {
    socket.emit('set_word', game_id, word);
    let dialog = document.querySelector('dialog');
    dialog.close();
}
function ack_reveal() {
    close_dialog();
    socket.emit('acknowledge_revealed_info', local_game_state.game_id);
}
function ask_question(game_id, question) {
    socket.emit('question', game_id, question);
}
function skip_question(game_id, question_id) {
    socket.emit('skip_question', game_id, question_id);
}
function undo_answer(game_id) {
    socket.emit('undo', game_id);
    close_dialog();
}
function send_start_req(game_id) {
    socket.emit('game_start', game_id);
}
function send_reset_req(game_id) {
    socket.emit('game_reset', game_id);

}
function set_player_target(game_id, target) {
    socket.emit('set_player_target', game_id, target);
}
function set_doppelganger_target(game_id, target) {
    socket.emit('set_player_target', game_id, target);
}
function vote_player(game_id, candidate) {
    socket.emit('vote', game_id, candidate);
}
function finish_vote(game_id) {
    socket.emit('finish_vote', game_id);
}
function toggle_question_autocomplete() {
    socket.emit('toggle_question_autocomplete');
}
function add_role(game_id, role) {
    socket.emit('add_role', game_id, role);
}
function remove_role(game_id, role) {
    socket.emit('remove_role', game_id, role);
}

function game_started_buttons() {
    // timer.start();
    let game_start_btn = document.getElementById('game_start');
    game_start_btn.hidden = true;
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

function stop_timer() {
    local_game_state.remaining_time_ms = 0;
    local_game_state.end_timestamp_ms = Date.now();
    let game_timer = document.getElementById('game_timer');
    game_timer.innerHTML = '00:00';
}

// TODO: Factor out the two timer functions to a single timer function
function start_timer() {
    // Set the date we're counting down to
    if (typeof game_timer_registered === 'undefined') {
        var game_timer_registered = true;
        let game_timer = document.getElementById('game_timer');
        console.log('refresh: ' + typeof refresh_timer)

        if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS' &&
            typeof refresh_timer === 'undefined') {
            local_game_state.end_timestamp_ms = Date.now() + local_game_state.remaining_time_ms;
            // Update the count down every 1 second
            const refresh_timer = setInterval(function () {
                local_game_state.remaining_time_ms = local_game_state.end_timestamp_ms - Date.now();
                console.log('Refresh for game timer should only happen 1/sec: ' + Date.now())

                // If the count down is over, write some text 
                if (local_game_state.game_state === 'VOTING') {
                    clearInterval(refresh_timer);
                    game_timer.innerHTML = '00:00';

                }
                if (local_game_state.remaining_time_ms <= 0) {
                    clearInterval(refresh_timer);
                    if (local_game_state.player_is_mayor) {
                        const start_vote_promise = new Promise(resolve => {
                            socket.emit('start_vote', local_game_state.game_id, (response) => {
                                if (response.status === 'OK') {
                                    resolve('Voting started');
                                }
                            });
                        })
                    }
                }
                if (local_game_state.remaining_time_ms > 0) {
                    game_timer.innerHTML = format_time(local_game_state.remaining_time_ms);
                } else {
                    game_timer.innerHTML = '00:00';
                }
            }, 1000);
        }
    }
}

function start_vote_timer() {
    if (typeof vote_timer_registered === 'undefined') {
        var vote_timer_registered = true;

        // Set the date we're counting down to
        let game_timer = document.getElementById('game_timer');

        if (local_game_state.game_state === 'VOTING' &&
            typeof refresh_vote_timer === 'undefined') {
            var refresh_vote_timer = setInterval(function () {
                local_game_state.remaining_vote_time_ms = local_game_state.end_vote_timestamp_ms - Date.now();

                // If the count down is over, write some text 
                if (local_game_state.remaining_vote_time_ms <= 0 ||
                    local_game_state.game_state === 'FINISHED') {
                    clearInterval(refresh_vote_timer);
                    game_timer.innerHTML = "00:00";
                    if (local_game_state.player_is_mayor) {
                        finish_vote(local_game_state.game_id);
                    }
                }
                if (local_game_state.remaining_vote_time_ms > 0) {
                    game_timer.innerHTML = format_time(local_game_state.remaining_vote_time_ms);
                } else {
                    game_timer.innerHTML = '00:00';
                }
            }, 1000);
        }
    }
}

function refresh_players(game_id) {
    let players = document.getElementById('players');
    socket.emit('get_players', game_id, (response) => {
        if (response.status === 'OK') {
            players.innerHTML = response.players_html;
        }
    });
}

function refresh_questions(game_id) {
    let questions_div = document.getElementById('questions_div');
    socket.emit('get_questions', game_id, (response) => {
        if (response.status === 'OK') {
            questions_div.innerHTML = response.questions_html;
        }
    });
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

    // Start top down on display
    let game_timer = document.getElementById('game_timer');
    if (local_game_state.remaining_time_ms > 0) {
        game_timer.innerHTML = format_time(local_game_state.remaining_time_ms);
    } else {
        game_timer.innerHTML = "00:00";
    }
    game_timer.hidden = false;
    refresh_players(local_game_state.game_id);
    let player_info = document.getElementById('player_info')
    player_info.hidden = false;

    let question_input = document.getElementById('question_input');
    question_input.hidden = true;
    let dialog_box = document.getElementById('dialog-box');
    dialog_box.hidden = true;
    let controls = document.getElementById('controls');
    controls.hidden = false;
    let dialog = document.querySelector('dialog');


    let roles_div = document.getElementById('roles')
    let nominate_for_mayor_btn = document.getElementById('nominate_for_mayor');
    if (local_game_state.mayor !== null) {
        nominate_for_mayor_btn.hidden = true;
    } else {
        if (local_game_state.spectating === true ||
            local_game_state.nominated_for_mayor === true) {
            nominate_for_mayor_btn.hidden = true;
        } else {
            nominate_for_mayor_btn.hidden = false;
        }
    }
    if (local_game_state.game_state === 'SETUP') {
        game_setup_buttons();
        refresh_questions(local_game_state.game_id);
        game_timer.innerHTML = format_time(local_game_state.timer * 1000)
        socket.emit('get_role_page', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                roles_div.hidden = false;
                roles_div.innerHTML = response.role_html;
            }
        });
    } else {
        game_started_buttons();
        roles_div.hidden = true;
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
    let footer_role_information = document.getElementById('footer_role_information');
    if (footer_role_information !== null) {
        socket.emit('get_footer', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                footer_role_information.innerHTML = response.reveal_html;
            } else {
                footer_role_information.innerHTML = '';
            }
        });
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
        if (typeof refresh_timer === 'undefined') {
            start_timer();
        }
        refresh_questions(local_game_state.game_id);
        if (!local_game_state.spectating && !local_game_state.player_is_mayor) {
            question_input.hidden = false;
        }
    }
    if (local_game_state.game_state === 'VOTING') {
        refresh_questions(local_game_state.game_id);
        stop_timer();
        start_vote_timer();
        socket.emit('get_voting_page', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                dialog_box.innerHTML = response.voting_html;
                dialog_box.hidden = false;
                controls.hidden = true;
            }
        });
    }
    if (local_game_state.game_state === 'FINISHED') {
        refresh_questions(local_game_state.game_id);
        socket.emit('get_results', local_game_state.game_id, (response) => {
            game_timer.innerHTML = "00:00"
            if (response.status === 'OK') {
                dialog_box.innerHTML = response.results_html;
                dialog_box.hidden = false;
                controls.hidden = true;
                let vote_details = document.getElementById('vote_details');
                if (vote_details !== null) {
                    vote_details.addEventListener("click", function () {
                        this.classList.toggle("active");
                        var content = this.nextElementSibling;
                        if (content.style.display === "block") {
                            content.style.display = "none";
                        } else {
                            content.style.display = "block";
                        }
                    });
                }
            }
        });
    }
    if (local_game_state.player_is_admin) {
        let admin_controls = document.getElementById('admin_controls');
        admin_controls.hidden = false;
        let nav_reset_game_btn = document.getElementById('nav_game_reset');
        nav_reset_game_btn.hidden = false;
        let reset_game_btn = document.getElementById('game_reset');
        let game_timer_settings = document.getElementById('game_timer_settings');
        if (local_game_state.game_state === 'SETUP') {
            game_timer_settings.hidden = false;
        } else {
            game_timer_settings.hidden = true;
        }
        if (local_game_state.game_state === 'FINISHED') {
            reset_game_btn.hidden = false;
            game_timer_settings.hidden = false;
        } else {
            reset_game_btn.hidden = true;
        }
        let boot_players = document.getElementById('boot_players');
        if (boot_players !== null) {
            boot_players.addEventListener("click", function () {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                socket.emit('get_bootable_players', local_game_state.game_id, (response) => {
                    if (response.status === 'OK') {
                        content.innerHTML = response.html;
                    }
                });
                if (content.style.display === "block") {
                    content.style.display = "none";
                } else {
                    content.style.display = "block";
                }
            });
        }


    }
    if (local_game_state.player_is_mayor) {
        let mayor_controls = document.getElementById('mayor_controls');
        let mayor_question = document.getElementById('mayor_question');
        if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS') {
            mayor_controls.hidden = false;
            socket.emit(
                'get_next_unanswered_question',
                local_game_state.game_id,
                (response) => {
                    if (response.status === 'OK') {
                        mayor_question.hidden = false;
                        mayor_question.innerHTML = response.question_html;
                    } else {
                        mayor_question.innerHTML = '';
                        mayor_question.hidden = true;
                    }
                });
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
        if (local_game_state.game_state == 'VOTING') {
            mayor_question.innerHTML = '';
            mayor_question.hidden = true;
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
            dialog.innerHTML = data;
            dialog.showModal();
        }
    });
    socket.on('mayor_question', function (data) {
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
    socket.on('game_state_update', function (data) {
        if (local_game_state.update_timestamp !== data.timestamp) {
            get_game_state(local_game_state.game_id);
        }
    });
    socket.on('refresh_players', function (data) {
        console.log(data);
        refresh_players(data);
    });
    socket.on('role_update', function (data) {
        if (local_game_state.game_id === data.game_id) {
            let role_count = document.getElementById('role_count_' + data.role);
            socket.emit('get_role_count', game_id, role, (response) => function () {
                if (response.status === 'OK') {
                    role_count.innerHTML = response.count;
                }
            });
        }
    });

    // Set event listeners
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
    var username_input = document.getElementById('username_change');
    if (username_input !== null) {
        username_input.addEventListener('keypress', function (event) {
            if (event.key === "Enter") {
                username_input.submit()
            }
        });
    }
    var game_timer_input = document.getElementById('game_timer_input');
    var timer_controls = document.getElementById('timer_controls');
    if (game_timer_input !== null) {
        game_timer_input.addEventListener('keypress', function (event) {
            if (event.key === "Enter") {
                set_timer(local_game_state.game_id, game_timer_input.value);
                if (timer_controls !== null) {
                    timer_controls.style.display = 'none';
                }
            }
        });
    }
    let nominate_for_mayor_btn = document.getElementById('nominate_for_mayor');
    nominate_for_mayor_btn.addEventListener('click', function () {
        const nominate_promise = new Promise((resolve, error) => {
            socket.emit('nominate_for_mayor', local_game_state.game_id, (response) => {
                if (response.status === 'OK') {
                    resolve(response.status);
                } else {
                    error(response.status + ': Unable to nominate. ' +
                        'Possibly already nominated.');
                }
            });
        })
        nominate_promise.then(
            (resolve) => {
                console.log('Successfully nominated: ' + resolve)
                nominate_for_mayor_btn.hidden = true;
            },
            (error) => {
                console.log(error)
            }
        )
    });
});