import numpy as np
import sys
import time
import pickle
import pandas as pd
import os
sys.path.append("../..")

from energy_spectrum_solver import energy_spectrum


def squarewell_benchmark(
        mode, gridincrements, neigbors,
        minimalgrid=None, Romberg=True):
    fval = lambda x: 0.  # return zero -- infinite square well

    energies = energy_spectrum(
        0., 1., fval, 1.,
        Romberg_integrator=Romberg,
        neighbors=neigbors,
        mode=mode,
        minimalgrid=minimalgrid,
        gridincrements=gridincrements,
        incrementfactor=None,
        verbose=0)
    numprint = 20
    analytical = np.pi**2/(2.*1.**2)*np.arange(1, len(energies)+1)**2
    diff = energies[:numprint]-analytical[:numprint]
    scaled_diff = np.abs(diff)*np.exp(-0.015*analytical[:numprint])
    loss = np.sum(scaled_diff)
    return loss


def harmonic_benchmark(
        mode, gridincrements, neigbors,
        minimalgrid=None, Romberg=True):
    # Harmonic potential
    fval = lambda x: 0.5*x**2

    energies = energy_spectrum(
        -50, 50, fval, 1.,
        Romberg_integrator=Romberg,
        neighbors=neigbors,
        mode=mode,
        minimalgrid=minimalgrid,
        gridincrements=gridincrements,
        incrementfactor=None,
        verbose=0)
    numprint = 20
    analytical = 0.5+np.arange(0, len(energies))
    diff = energies[:numprint]-analytical[:numprint]
    scaled_diff = 1e9*np.abs(diff)*np.exp(-0.5*analytical[:numprint])
    loss = np.sum(scaled_diff)
    return loss


def does_entry_exists(
        df, mode, gridincrements, neigbors,
        Romberg, minimalgrid):

    lookup = df[
        (df['mode'] == mode) &
        (df['gridincrements'] == gridincrements) &
        (df['neigbors'] == neigbors) &
        (df['minimalgrid'] == minimalgrid) &
        ((df['Romberg']) == Romberg)
    ]
    if len(lookup) > 0:
        return True
    else:
        return False


fn = "optimize_calculated_results.pckl"
if os.path.exists(fn):
    df = pickle.load(open(fn, 'rb'))
else:
    df = pd.DataFrame(
        columns=[
            'i',
            'mode', 'gridincrements', 'neigbors', "timing", "loss"])
    df = df.set_index('i')

if 0:
    for mode in range(0, 4):
        for gridincrements in range(2, 6):
            for neigbors in range(1, 7):
                Romberg = True
                minimalgrid = None
                if does_entry_exists(
                        df, mode, gridincrements, neigbors,
                        Romberg, minimalgrid):
                    continue

                print('mode: %i  gridincrements: %i neigbors: %i' % (
                    mode, gridincrements, neigbors),)

                t0 = time.time()
                loss = np.square(
                    harmonic_benchmark(mode, gridincrements, neigbors)
                    * squarewell_benchmark(mode, gridincrements, neigbors))
                log_loss = np.log(loss)
                t1 = time.time()
                timing = t1-t0
                df = df.append(
                    pd.DataFrame({
                        'mode': mode,
                        'gridincrements': gridincrements,
                        'neigbors': neigbors,
                        'timing': timing,
                        'loss': loss,
                        'log_loss': log_loss,
                        'Romberg': Romberg, },
                        index=[0]))

                print(
                    ' ----> '
                    'timing: %.2f log_loss: %.2f' % (
                        timing, log_loss)
                )
                pickle.dump(df, open(fn, 'wb'))


grids = list(2**np.array(range(7, 13)))

for minimalgrid in grids:
    for neigbors in range(1, 7):
        Romberg = False
        gridincrements = 0
        mode = -100  # FD
        if does_entry_exists(
                df, mode, gridincrements, neigbors,
                Romberg, minimalgrid):
            continue

        print('Romberg %r minimalgrid: %i neigbors: %i' % (
            Romberg, minimalgrid, neigbors),)

        t0 = time.time()
        loss = np.square(
            harmonic_benchmark(
                mode, gridincrements, neigbors,
                minimalgrid=minimalgrid, Romberg=Romberg)
            * squarewell_benchmark(
                mode, gridincrements, neigbors,
                minimalgrid=minimalgrid, Romberg=Romberg))
        log_loss = np.log(loss)
        t1 = time.time()
        timing = t1-t0
        df = df.append(
            pd.DataFrame({
                'mode': mode,
                'Romberg': Romberg,
                'gridincrements': gridincrements,
                'minimalgrid': minimalgrid,
                'neigbors': neigbors,
                'timing': timing,
                'loss': loss,
                'log_loss': log_loss, },
                index=[0]))

        print(
            ' ----> '
            'timing: %.2f log_loss: %.2f' % (
                timing, log_loss)
        )
        pickle.dump(df, open(fn, 'wb'))
