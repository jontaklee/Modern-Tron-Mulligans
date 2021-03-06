#!/usr/bin/env python3 v2.0
# -*- coding: utf-8 -*-
"""
Simulate hands using the Vancouver mulligan

Returns turn on which Tron is achieved

@author: jonathan t. lee - https://github.com/jontaklee

version 2.0: updated for Once Upon a Time
"""
import numpy as np

import card_classes
from card_classes import TronDeck, Chromatic


# helper function to count tron lands in play
def tron_check(zone):
    
    card_names = {}
    for card in zone:
        card_names[card.name] = card_names.get(card.name, 0) + 1
    
    tron_set = set(['Urza\'s Tower', 'Urza\'s Mine', 'Urza\'s Power Plant'])
    return tron_set.difference(card_names)

# simulates the vancouver mulligan scry rule
def vancouver_scry(library, hand):
    
    temp = library.deck[0]
    names = [card.name for card in hand]
    
    # determine which Tron lands aren't in the starting hand
    tron_needed = tron_check(hand)
    
    num_lands = [card.card_type for card in hand].count('land')
    g_sources = set(['Forest', 'Chromatic Star', 'Chromatic Sphere'])
    
    # code below doesn't care what to do if you already have Tron in hand

    # keep on top if card is a Tron land
    if temp.name in tron_needed:
        top = True
        
    # bottom anything that's not a Tron land if hand is a 1-lander
    elif num_lands < 2:
        top = False
        
    # always top Expedition map if hand can cast and activate it
    elif temp.name == 'Expedition Map':
        top = True
        
    # keep Sylvan Scrying if hand can cast it
    elif temp.name == 'Sylvan Scrying' or temp.name == 'Ancient Stirrings':
        if len(g_sources.intersection(set(names))) > 0:
            top = True
        
        else:
            top = False
        
    # only keep Star/Sphere if hand contains Scrying/Stirrings but no green source
    elif temp.name == 'Chromatic Star' or temp.name == 'Chromatic Sphere':
        if 'Sylvan Scrying' in names or 'Ancient Stirrings' in names \
        and len(g_sources.intersection(set(names))) == 0:
            top = True
        
        else: 
            top = False
                
    # bottom everything else
    else: 
        top = False
    
    if top is False:
        library.scry_bottom()
    
def sim_turn(hand, deck, bfield, turn):
        
    manapool = [card.card_type for card in bfield].count('land')
    g_mana = [card.name for card in bfield].count('Forest')

    land_drop = False
    plays = True
    
    # cast Once Upon a Time for free
    if turn == 0:
        hand_names = [card.name for card in hand]
        if 'Once Upon a Time' in hand_names:
            card = hand[hand_names.index('Once Upon a Time')]
            card.cast(hand, deck, bfield)
    
    # continue until no plays are available
    while plays:
        plays = False
        
        hand_names = [card.name for card in hand]
        bfield_names = [card.name for card in bfield]
        
        tron_needed = tron_check(bfield)
        if len(tron_needed) == 0 and manapool >= 3:
            return(True)
        
        priority = (('Expedition Map', 'ability'), ('Sylvan Scrying', 'cast'), 
                    ('Expedition Map', 'cast'), ('Ancient Stirrings', 'cast'), ('OUaT', 'cast'),
                    ('Chromatic Star', 'ability'), ('Chromatic Sphere', 'ability'),
                    ('Chromatic Star', 'cast'), ('Chromatic Sphere', 'cast'),
                    ('Relic of Progenitus', 'ability'), ('Relic of Progenitus', 'cast'),
                    ('Forest', 'play'), ('Ghost Quarter', 'play'), ('Sanctum of Ugin', 'play'),
                    ('Urza\'s Tower', 'play'), ('Urza\'s Mine', 'play'), ('Urza\'s Power Plant', 'play'))
        
        # play a tron land from hand if already available
        for card_name in list(tron_needed):
            if card_name in hand_names and land_drop is False:
                card = hand[hand_names.index(card_name)]
                card.play(hand, bfield)
                
                #update hand names and remaining tron pieces needed
                hand_names.pop(hand_names.index(card_name))
                tron_needed = tron_check(bfield)
                
                manapool += 1
                
                if len(tron_needed) == 0 and manapool >= 3:
                    return(True)
                    
                land_drop = True
                    
                break
        
        # play a card and return to the top of the loop 
        for card in priority:
            
            field = card[1]
            name = card[0]
            
            # for activated abilities of cards in play
            if field == 'ability' and name in bfield_names:
                card = bfield[bfield_names.index(name)]
                if manapool >= card.amc:
                    card.ability(hand, deck, bfield)
                    manapool -= card.amc
                    if type(card) == Chromatic:
                        manapool += 1
                        g_mana += 1
                    plays = True
                    break
            
            # for casting a spell in hand
            if field == 'cast' and name in hand_names:
                card = hand[hand_names.index(name)]
                if manapool >= card.cmc and g_mana >= card.gmc:
                    card.cast(hand, deck, bfield)
                    manapool -= card.cmc
                    g_mana -= card.gmc
                    plays = True
                    break
            
            # for playing a land that's not a missing Tron land (last option)
            if field == 'play' and name in hand_names and land_drop is False:
                card = hand[hand_names.index(name)]
                card.play(hand, bfield)
                plays = True
                land_drop = True
                manapool += 1
                if card.name == 'Forest':
                    g_mana += 1
                break
            
    return(False)


def sim_magic(handsize, on_draw):
    '''
    handsize: starting handsize (int)
    on_draw: boolean
    '''
    library = TronDeck()
    bfield = []
    
    hand = library.draw_opener(handsize)
    starting_hand = [card.name for card in hand]
    
    # comment out to disable vancouver scry
    '''
    if handsize < 7:
        vancouver_scry(library, hand)
    '''
    
    tron_achieved = False
    turn = 0
    
    # simulates playing until Tron is in play
    while tron_achieved is False:
        
        if on_draw or turn != 0:
            library.draw(hand)
            
        tron_achieved = sim_turn(hand, library, bfield, turn)
            
        turn += 1
    
    return (starting_hand, turn)


def estimate_turns(on_draw):
    # on_draw -- True/False
    
    for i in range(7, 2, -1):
        turns = []
        for n in range(5000):
            res = sim_magic(i, on_draw)
            turns.append(res[1])
        #return np.mean(turns), np.std(turns)
        print(i, 'card hand:', np.mean(turns), 'turns')

def turn3_estimate(on_draw, n):
    # on_draw -- True/False
    for i in range(7, 2, -1):
        turns = []
        for num in range(n):
            res = sim_magic(i, on_draw)
            turns.append(res[1])
        #return np.mean(turns), np.std(turns)
        print(i, 'card hand:', turns.count(3)/n)
        
def turn4_estimate(on_draw, n):
    # on_draw -- True/False
    for i in range(7, 2, -1):
        turns = []
        for num in range(n):
            res = sim_magic(i, on_draw)
            turns.append(res[1])
        #return np.mean(turns), np.std(turns)
        print(i, 'card hand:', round(turns.count(3)/n + turns.count(4)/n, 3))
    

def main():
    options = {'y':True, 'n':False}
    while 1:
        draw = input('on the draw? y/n: ').lower()
        if draw in options: break
        else: print('input must be y or n')
    print('simulating hands:')
    estimate_turns(options[draw])
    
    
if __name__ == '__main__':
    main()
              