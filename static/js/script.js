var socket = io.connect({ autoconnect: true });
var local_game_state = {};
var local_time_skew = 0;
var canned_questions = [
    'Can it fly?',
    'Can you control it?',
    'Can you own more than one?',
    'Can you own one?',
    'Can you purchase it?',
    'Can you see it?',
    'Can you touch it?',
    'Do you have more than one?',
    'Do you have one?',
    'Does it have feelings?',
    'Does it have opposable digits?',
    'Has it ever been alive?',
    'Is it a concept?',
    'Is it a plant?',
    'Is it a proper noun?',
    'Is it a tool?',
    'Is it an action?',
    'Is it alive?',
    'Is it bigger than a bread box?',
    'Is it bigger than a planet?',
    'Is it considered expensive?',
    'Is it edible?',
    'Is it food?',
    'Is it found in a house?',
    'Is it found on Earth?',
    'Is it larger than a house?',
    'Is it mechanical?',
    'Is it something that is used daily?',
    'Is it taught in elementary school?',
    'Is it taught in high school?',
    'Is the person alive?',
    'Would you find it in a garage?',
];
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
function start_vote(game_id) {
    socket.emit('start_vote', game_id);
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

// Stolen wholesale from https://www.w3schools.com/howto/howto_js_autocomplete.asp
function autocomplete(inp, arr) {
    if (inp === null) {
        return
    }

    var currentFocus;
    inp.addEventListener("input", function (e) {
        var a, b, i, val = this.value;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        if (!val) { return false; }
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", this.id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        this.parentNode.appendChild(a);
        /*for each item in the array...*/
        for (i = 0; i < arr.length; i++) {
            /*check if the item starts with the same letters as the text field value:*/
            if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
                /*create a DIV element for each matching element:*/
                b = document.createElement("DIV");
                /*make the matching letters bold:*/
                b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
                b.innerHTML += arr[i].substr(val.length);
                /*insert a input field that will hold the current array item's value:*/
                b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
                /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function (e) {
                    /*insert the value for the autocomplete text field:*/
                    inp.value = this.getElementsByTagName("input")[0].value;
                    if (inp.value != "") {
                        socket.emit('question', local_game_state.game_id, inp.value);
                        inp.value = "";
                    }
                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
    });
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function (e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
                /*and simulate a click on the "active" item:*/
                if (x) x[currentFocus].click();
            }
            // TODO: Add the ability to enter to submit.
        }
    });
    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (var i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }
    function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
            if (elmnt != x[i] && elmnt != inp) {
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }
    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
    });
}

// TODO: Factor out the two timer functions to a single timer function
function start_timer() {
    // Set the date we're counting down to
    let game_timer = document.getElementById('game_timer');

    if (local_game_state.game_state === 'DAY_PHASE_QUESTIONS' &&
        typeof refresh_timer === 'undefined') {
        local_game_state.end_timestamp_ms = Date.now() + local_game_state.remaining_time_ms;
        // Update the count down every 1 second
        var refresh_timer = setInterval(function () {
            local_game_state.remaining_time_ms = local_game_state.end_timestamp_ms - Date.now();

            // If the count down is over, write some text 
            if (local_game_state.remaining_time_ms <= 0 ||
                local_game_state.game_state === 'VOTING') {
                clearInterval(refresh_timer);
                game_timer.innerHTML = "00:00";
                if (local_game_state.player_is_mayor) {
                    start_vote(local_game_state.game_id);
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

function start_vote_timer() {
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
            nominate_for_mayor_btn.addEventListener('click', function () {
                socket.emit('nominate_for_mayor', local_game_state.game_id)
                nominate_for_mayor_btn.hidden = true;
            });
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
        start_timer();
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
            html = data;
            html += '<br><button type="button" class="mdl-button close"';
            html += ' onclick="close_dialog()">OK</button>';
            dialog.innerHTML = html;

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
});