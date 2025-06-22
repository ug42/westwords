var socket = io.connect({ autoconnect: true });
var local_game_state = {};
var timer_running = false;

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
    let modalElement = document.getElementById('main-modal');
    if (modalElement) {
        var myModalInstance = bootstrap.Modal.getInstance(modalElement);
        if (myModalInstance) {
            myModalInstance.hide();
        }
    }
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
    // let dialog = document.querySelector('dialog'); // No longer needed
    // dialog.close(); // No longer needed
    close_dialog(); // Use the updated global close_dialog
}
function ack_reveal() {
    close_dialog();
    socket.emit('acknowledge_revealed_info', local_game_state.game_id);
}
function ask_question(game_id, question, force) {
    socket.emit('question', game_id, question, force, (response) => {
        if (response.status === 'DUPLICATE') {
            let modalElement = document.getElementById('main-modal');
            if (modalElement) {
                var modalBody = modalElement.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.innerHTML = response.html;
                } else {
                    console.error('Modal body not found for ID main-modal');
                }
                // Ensure modal title is appropriate or cleared for generic content
                var modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = 'Duplicate Question?'; // Or extract from response.html if possible
                }
                var myModal = new bootstrap.Modal(modalElement);
                myModal.show();
            }
        }
    });
    document.getElementById('question').value = "";
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
    close_dialog();
}
function set_doppelganger_target(game_id, target) {
    socket.emit('set_player_target', game_id, target);
    close_dialog();
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
    timer_running = false;
}

// TODO: Factor out the two timer functions to a single timer function
function start_timer() {
    if (timer_running === false) {
        timer_running = true;
        let game_timer = document.getElementById('game_timer');
        console.log('refresh: ' + typeof refresh_timer)

        if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS' &&
            typeof refresh_timer === 'undefined') {
            local_game_state.end_timestamp_ms = Date.now() + local_game_state.remaining_time_ms;
            // Update the count down every 1 second
            const refresh_timer = setInterval(function () {
                local_game_state.remaining_time_ms = local_game_state.end_timestamp_ms - Date.now();

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
    if (timer_running === false) {
        timer_running = true;

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

// TODO: Fix this. This should force a reload if someone is hitting the back
// button, but it's not working.
(function () {
    window.onpageshow = function (event) {
        if (event.persisted) {
            window.location.reload();
        }
    };
})();

function refresh_game_state(g) {
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
    let roles_div = document.getElementById('roles')
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

    // Show My Role button visibility
    const showRoleButton = document.getElementById('show_role_button');
    if (showRoleButton) {
        if (local_game_state.game_state === 'SETUP' || local_game_state.game_state === 'FINISHED') {
            showRoleButton.style.display = 'none';
        } else {
            // Show button if player is not spectating. If they are spectating, their role is 'Spectator' and can be shown.
            // The button is part of the 'controls' div, which is hidden for spectators indirectly by other logic.
            // However, explicit control here is good.
            if (local_game_state.spectating === true) {
                 showRoleButton.style.display = 'none';
            } else {
                 showRoleButton.style.display = 'inline'; // Or 'block'
            }
        }
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
                footer_role_information.innerHTML = response.footer_html;
            } else {
                footer_role_information.innerHTML = '';
            }
        });
    }

    if (local_game_state.game_state === 'NIGHT_PHASE_DOPPELGANGER' ||
        local_game_state.game_state === 'NIGHT_PHASE_TARGETTING') {
        socket.emit('get_night_action_page', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                let modalElement = document.getElementById('main-modal');
                if (modalElement) {
                    var modalBody = modalElement.querySelector('.modal-body');
                    if (modalBody) {
                        modalBody.innerHTML = response.night_action_html;
                    } else {
                        console.error('Modal body not found for ID main-modal');
                    }
                    var modalTitle = modalElement.querySelector('.modal-title');
                    if (modalTitle) {
                        modalTitle.textContent = 'Night Action';
                    }
                    var myModal = new bootstrap.Modal(modalElement);
                    myModal.show();
                }
            }
        });
    }
    if (local_game_state.game_state === 'NIGHT_PHASE_REVEAL') {
        socket.emit('get_player_revealed_information', local_game_state.game_id, (response) => {
            if (response.status === 'OK') {
                let modalElement = document.getElementById('main-modal');
                if (modalElement) {
                    var modalBody = modalElement.querySelector('.modal-body');
                    if (modalBody) {
                        modalBody.innerHTML = response.reveal_html;
                    } else {
                        console.error('Modal body not found for ID main-modal');
                    }
                    var modalTitle = modalElement.querySelector('.modal-title');
                    if (modalTitle) {
                        modalTitle.textContent = 'Role Information';
                    }
                    var myModal = new bootstrap.Modal(modalElement);
                    myModal.show();
                }
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
                let modalElement = document.getElementById('main-modal');
                if (modalElement) {
                    if (response.status === 'OK') {
                        var modalBody = modalElement.querySelector('.modal-body');
                        if (modalBody) {
                            modalBody.innerHTML = response.word_html;
                        } else {
                            console.error('Modal body not found for ID main-modal');
                        }
                        var modalTitle = modalElement.querySelector('.modal-title');
                        if (modalTitle) {
                            modalTitle.textContent = 'Choose a Word';
                        }
                        var myModal = new bootstrap.Modal(modalElement);
                        myModal.show();
                    }
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
    // MDL Dialog polyfill and initial show/close removed.
    // var dialog = document.querySelector('dialog'); // Old MDL
    // if (!dialog.showModal) { // Old MDL
    //     dialogPolyfill.registerDialog(dialog); // Old MDL
    // } // Old MDL
    // dialog.showModal(); // Old MDL
    // dialog.close(); // Old MDL

    // var snackbarContainer = document.querySelector('#demo-toast-example'); // Will be handled in Phase 2

    socket.on('connect', function () {});
    socket.on('disconnect', function (data) {
        console.log('Socket disconnected.');
    });
    socket.on('user_info', function (message) {
        // snackbarContainer.MaterialSnackbar.showSnackbar({ message: message }); // Old MDL
        var toastLiveExample = document.getElementById('toast-container'); // ID of the Bootstrap toast container
        if (toastLiveExample) {
            var toastBody = toastLiveExample.querySelector('.toast-body');
            if (toastBody) {
                toastBody.textContent = message; // Assuming message is plain text
            } else {
                console.error('Toast body not found in #toast-container');
            }
            var toast = new bootstrap.Toast(toastLiveExample);
            toast.show();
        } else {
            console.error('Toast element #toast-container not found');
        }
    });


    socket.on('mayor_error', function (data) {
        if (local_game_state.player_is_mayor === true) {
            let modalElement = document.getElementById('main-modal');
            if (modalElement) {
                var modalBody = modalElement.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.innerHTML = data; // Assuming data is HTML string
                } else {
                    console.error('Modal body not found for ID main-modal');
                }
                var modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = 'Mayor Notification';
                }
                var myModal = new bootstrap.Modal(modalElement);
                myModal.show();
            }
        }
    });
    socket.on('mayor_question', function (data) {
        // This event seems to be for simple text, not full HTML for modal body.
        // For now, will put it in modal body, but might need adjustment if it's just a string.
        if (local_game_state.player_is_mayor === true) {
            let modalElement = document.getElementById('main-modal');
            if (modalElement) {
                var modalBody = modalElement.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.innerHTML = data; // Assuming data is HTML string
                } else {
                    console.error('Modal body not found for ID main-modal');
                }
                var modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = 'Mayor Question';
                }
                var myModal = new bootstrap.Modal(modalElement);
                myModal.show();
            }
        }
    });
    socket.on('admin_error', function (data) {
        if (local_game_state.player_is_admin === true) {
            let modalElement = document.getElementById('main-modal');
            if (modalElement) {
                var modalBody = modalElement.querySelector('.modal-body');
                if (modalBody) {
                    modalBody.innerHTML = data; // Assuming data is HTML string
                } else {
                    console.error('Modal body not found for ID main-modal');
                }
                var modalTitle = modalElement.querySelector('.modal-title');
                if (modalTitle) {
                    modalTitle.textContent = 'Admin Notification';
                }
                var myModal = new bootstrap.Modal(modalElement);
                myModal.show();
            }
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
            socket.emit('get_role_count', data.game_id, data.role, (response) => {
                if (response.status === 'OK') {
                    document.getElementById(response.element_id).innerHTML = response.count;
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
                    ask_question(local_game_state.game_id, question.value, false);
                }
            }
        });
        document.getElementById('question_submit').addEventListener('click', function () {
            if (question.value != "") {
                ask_question(local_game_state.game_id, question.value, false);
            }
        });
    }
    var username_change = document.getElementById('username_change');
    if (username_change !== null) {
        username_change.addEventListener('submit', function (event) {
            let titlebar_username = document.getElementById('titlebar-username');
            let username = document.getElementById('username_input').value;
            titlebar_username.innerHTML = username;
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
    if (nominate_for_mayor_btn !== null) {
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
    }
    // New function to request role information
    window.showMyRole = function() {
        const pathParts = window.location.pathname.split('/');
        let gameId = pathParts[pathParts.length - 1];
        // Basic validation: if the last part is 'game' or empty, try the second to last.
        // This handles cases like /game/gameId or /game/gameId/
        if (gameId.toLowerCase() === 'game' || gameId.trim() === '') {
            if (pathParts.length > 1) {
                gameId = pathParts[pathParts.length - 2];
            } else {
                 console.error('Could not determine game_id from URL:', window.location.pathname);
                 // Attempt to use local_game_state.game_id if available
                 if (local_game_state && local_game_state.game_id) {
                     gameId = local_game_state.game_id;
                     console.log('Using game_id from local_game_state:', gameId);
                 } else {
                    alert('Error: Could not determine Game ID.');
                    return;
                 }
            }
        }
        
        if (!gameId || gameId.trim() === '') {
            console.error('Error: Game ID is empty or invalid from URL and local_game_state.');
            alert('Error: Game ID is missing or invalid.');
            return;
        }

        console.log('Requesting role for game:', gameId);
        socket.emit('get_my_role', gameId);
    }

    // New listener for receiving role information
    socket.on('my_role_info', function(data) {
        console.log('Received my_role_info:', data);
        let dialogBox = document.getElementById('dialog-box'); 
        if (!dialogBox) {
            console.error('Element with ID "dialog-box" not found.');
            // alert('Error: UI element for displaying role information is missing.');
            return;
        }

        let htmlContent = '';
        if (data.status === 'OK') {
            // Ensure data fields exist to prevent 'undefined' in output
            const roleImage = data.role_image || 'static/img/unknown.png'; // Fallback image
            const roleName = data.role_name || 'Role Name Not Available';
            const roleDescription = data.role_description || 'No description provided.';

            htmlContent = `
                <div style="text-align: center; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 300px; margin: 20px auto;">
                    <img src="${roleImage}" alt="${roleName}" style="max-width: 100px; max-height: 100px; margin-bottom: 15px; border-radius: 4px; object-fit: contain;">
                    <h3 style="margin-top: 0; margin-bottom: 10px; color: #333;">${roleName}</h3>
                    <p style="margin-bottom: 20px; color: #555; font-size: 0.9em; white-space: pre-wrap;">${roleDescription}</p>
                    <button onclick="closeRoleDialog()" style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Close</button>
                </div>
            `;
        } else {
            console.error('Error getting role:', data.message);
            const errorMessage = data.message || 'An unknown error occurred while fetching your role.';
            htmlContent = `
                <div style="text-align: center; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 300px; margin: 20px auto;">
                    <h3 style="margin-top: 0; margin-bottom: 10px; color: #d9534f;">Error Retrieving Role</h3>
                    <p style="margin-bottom: 20px; color: #555; font-size: 0.9em;">${errorMessage}</p>
                    <button onclick="closeRoleDialog()" style="padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Close</button>
                </div>
            `;
        }
        dialogBox.innerHTML = htmlContent;
        dialogBox.hidden = false; 
        dialogBox.style.display = 'block'; 
    });

    // New helper function to close the role dialog (dialog-box div)
    window.closeRoleDialog = function() {
        let dialogBox = document.getElementById('dialog-box');
        if (dialogBox) {
            dialogBox.innerHTML = ''; 
            dialogBox.style.display = 'none'; 
            dialogBox.hidden = true; 
        }
    }
});