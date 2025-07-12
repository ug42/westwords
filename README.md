# Westwords

Westwords is a social deduction word guessing game, similar to 20 questions, but with werewolves, seers, and the like. This game is heavily inspired by the board game Werewords.

## How to Play

1.  **Setup:**
    *   Players are assigned roles.
    *   One player is designated as the Mayor.
    *   The Mayor is shown a list of secret words and chooses one.

2.  **Night Phase:**
    *   Certain roles perform their night actions.
    *   The Werewolves learn the secret word.
    *   The Seer and Apprentice Seer (if the Mayor is a Seer) learn the secret word.
    *   The Fortune Teller learns the first letter of the secret word.
    *   Other roles with night actions perform them.

3.  **Day Phase:**
    *   Players take turns asking the Mayor "yes" or "no" questions to guess the secret word.
    *   The Mayor can only answer with "Yes", "No", "Maybe", "So Close", or "So Far" tokens.
    *   There is a limited number of "Yes" and "No" tokens.

4.  **Voting Phase:**
    *   If the players guess the secret word before time runs out or the tokens are depleted, the Village team wins, unless the Werewolves can identify and vote to eliminate the Seer or Fortune Teller.
    *   If the players do not guess the secret word, the Werewolf team wins, unless the players can identify and vote to eliminate a Werewolf.

## Roles

### Village Team

*   **Villager:** An ordinary villager. Asks questions, tries to guess the word. Wins with the Village team.
*   **Seer:** Knows the secret word. If the Village team guesses the word, the Werewolves can win by eliminating the Seer.
*   **Apprentice:** Becomes the Seer if the Mayor is a Seer.
*   **Fortune Teller:** Knows the first letter of the secret word. If the Village team guesses the word, the Werewolves can win by eliminating the Fortune Teller.
*   **Beholder:** Knows which players are the Apprentice, Seer, and Fortune Teller, but not who has which role.
*   **Mason:** Knows who the other Masons are.
*   **Esper:** Can choose a player to reveal their role to.
*   **Doppelganger:** Can copy another player's role and abilities.

### Werewolf Team

*   **Werewolf:** Knows the secret word and the other Werewolves. Tries to mislead the other players.
*   **Minion:** Aligned with the Werewolves, but doesn't know who they are. The Werewolves don't know the Minion either.

## Screenshots

**Game Setup:**
![Game Setup](https://via.placeholder.com/800x600.png?text=Game+Setup)

**Role Reveal:**
![Role Reveal](https://via.placeholder.com/800x600.png?text=Role+Reveal)

**Day Phase:**
![Day Phase](https://via.placeholder.com/800x600.png?text=Day+Phase)

**Voting:**
![Voting](https://via.placeholder.com/800x600.png?text=Voting)

**Results:**
![Results](https://via.placeholder.com/800x600.png?text=Results)

## Win Conditions

*   **Village Team wins if:**
    *   They guess the secret word and the Werewolves do not eliminate the Seer or Fortune Teller.
    *   They do not guess the secret word, but they vote to eliminate a Werewolf.

*   **Werewolf Team wins if:**
    *   The Village team does not guess the secret word and the players do not eliminate a Werewolf.
    *   The Village team guesses the secret word, and the Werewolves successfully vote to eliminate the Seer or Fortune Teller.
