"""Library for solving the 1d schrodinger equation using finite Distance
and the Romberg integration correction.
"""

from __future__ import print_function

import numpy as np


lapjj = [
    [0],
    [-2.0, 1.0],
    [-5./2, 4./3, -1./12],
    [-49./18, 3./2, -3./20, 1./90],
    [-205./72, 8./5, -1./5, 8./315, -1./560],
    [-5269./1800, 5./3, -5./21, 5./126, -5./1008, 1./3150],
    [-5369./1800, 12./7, -15./56, 10./189, -1./112, 2./1925, -1./16632]]

lapbli = [
    [0],
    [-2.0, 1.0],
    [-5./2, 4./3, -1./12],
    [-490./180, 270./180, -27./180, 2./180],
    [-14350./5040, 8064./5040, -1008./5040, 128./5040, -9./5040],
    [-73766./25200, 42000./25200, -6000./25200, 1000./25200, -125./25200,
        8./25200],
    [-2480478./831600, 1425600./831600, -222750./831600, 44000./831600,
        -7425./831600, 864./831600, -50./831600],
    [-228812298./75675600, 132432300./75675600, -22072050./75675600,
        4904900./75675600, -1003275./75675600, 160524./75675600,
        -17150./75675600, 900./75675600]]

boundarycorr = [
    [0],
    [0],
    [10./12, -15./12, -4./12, 14./12, -6./12, 1./12],
    [126./180, -70./180, -486./180, 855./180, -670./180, 324./180, -90./180,
        11./180],
    [3044./5040, 2135./5040, -28944./5040, 57288./5040, -65128./5040,
        51786./5040, -28560./5040, 10424./5040, -2268./5040, 223./5040],
    [13420./25200, 29513./25200, -234100./25200, 540150./25200,
        -804200./25200, 888510./25200, -731976./25200, 444100./25200,
        -192900./25200, 56825./25200, -10180./25200, 838./25200],
    [397020./831600, 1545544./831600, -11009160./831600, 29331060./831600,
        -53967100./831600, 76285935./831600, -83567088./831600,
        70858920./831600, -46112220./831600, 22619850./831600,
        -8099080./831600, 1999044./831600, -304260./831600, 21535./831600],
    [32808524./75675600, 188699914./75675600, -1325978220./75675600,
        4020699410./75675600, -8806563220./75675600, 15162089943./75675600,
        -20721128428./75675600, 22561929390./75675600, -19559645820./75675600,
        13424150740./75675600, -7206307108./75675600, 2963338014./75675600,
        -901775420./75675600, 191429035./75675600, -25318020./75675600,
        1571266./75675600]]


def energy_spectrum(
        xmin, xmax,
        fval, Hcoeff,
        mode='fast',
        Romberg_integrator=None,
        neighbors=None,
        minimalgrid=None,
        gridincrements=None,
        incrementfactor=None,
        verbose=1):

    """Calculate energy spectrum

    Args:
        xmin (float): lower end of domain
        xmax (float): upper end of domain
        fval (object): function for right hand side (RHS)
        Hcoeff ():coefficient to multiply the FD matrix with
        mode (str, int): mode for calculation
            Use 'fast' or 'accurate' mode
            Accurate is ~40x slower than fast but includes more
            energies (good for very sloppy modes) and higher
            accuracy.
            ! See benchmark test for why these modes were chosen.

        minimalgrid (int): number of points in minimal grid
        neighbours -- order of FD solver
            (higher convergence for more neighbours)
        gridincrements (int): num of increments
        incrementfactor (float): grid increment factor
    Returns:
        eigenvalue spectrum (numpy array)
    """

    modes = {

        'fast': {
            'minimalgrid': 1024,
            'gridincrements': 0,
            'incrementfactor': None,
            'neighbors': 6,
            'Romberg_integrator': False},

        'accurate': {
            'minimalgrid': 2048,
            'gridincrements': 0,
            'incrementfactor': None,
            'neighbors': 6,
            'Romberg_integrator': False},

        # 'fast': {
        #     'minimalgrid': 728,
        #     'gridincrements': 2,
        #     'incrementfactor': 4.0/3.0,
        #     'neighbors': 6, },

        # 'accurate': {
        #     'minimalgrid': 3124,
        #     'gridincrements': 2,
        #     'incrementfactor': 6.0/5.0,
        #     'neighbors': 4, },

        # Modes used for testing.
        # Not recommended!
        -1: {
            'minimalgrid': 728,
            'gridincrements': 2,
            'incrementfactor': 4.0/3.0},
        0: {
            'minimalgrid': 546,
            'gridincrements': 6,
            'incrementfactor': 4.0/3.0},
        1: {
            'minimalgrid': 728,
            'gridincrements': 5,
            'incrementfactor': 4.0/3.0},
        2: {
            'minimalgrid': 1023,
            'gridincrements': 5,
            'incrementfactor': 5.0/4.0},
        3: {
            'minimalgrid': 3124,
            'gridincrements': 5,
            'incrementfactor': 6.0/5.0},
        # finite difference mode
        -100: {
            'minimalgrid': 1024,
            'gridincrements': 0,
            'incrementfactor': 0,
        },
    }

    assert mode in modes.keys()

    if minimalgrid is None:
        minimalgrid = modes[mode]['minimalgrid']
    if gridincrements is None:
        gridincrements = modes[mode]['gridincrements']
    if incrementfactor is None:
        incrementfactor = modes[mode]['incrementfactor']
    if neighbors is None:
        neighbors = modes[mode].get('neighbors', 2)
    if Romberg_integrator is None:
        Romberg_integrator = modes[mode].get('Romberg_integrator', False)
    # print('mode', mode)
    # print('Romberg_integrator', Romberg_integrator)
    # print('neighbors', neighbors)
    # print('minimalgrid', minimalgrid)
    # print('gridincrements', gridincrements)
    # print('incrementfactor', incrementfactor)

    if Romberg_integrator:
        eigenarray = np.zeros((gridincrements+1, minimalgrid), float)
        pointarray = np.array(
            (minimalgrid+1)
            * incrementfactor**np.arange(0, gridincrements+1)-0.5, int)

        # check that these are identical, otherwise convergence is poor:
        # This has been checked for the predefined modes
        realincrementfactors = np.zeros(len(pointarray)-1)
        for i in range(len(realincrementfactors)):
            realincrementfactors[i] = (pointarray[i+1]+1.0)/(pointarray[i]+1.0)
        if verbose > 1:
            print('realincrementfactors', realincrementfactors)

        # Here we make the bare solution
        for i in range(gridincrements+1):
            eigenarray[i] = FDsolver(
                xmin, xmax, pointarray[i], fval, Hcoeff,
                neighbors=neighbors)[:minimalgrid]

        print(np.shape(eigenarray))

        extrapolatedspectrum, relativeerrors = RombergSpectrumIntegrator(
            eigenarray, realincrementfactors[1], exact=None)

        energy_spectrum = extrapolatedspectrum
    else:
        # Simple finite difference method.
        energy_spectrum = FDsolver(
            xmin, xmax, minimalgrid, fval, Hcoeff,
            neighbors=neighbors)

    return energy_spectrum


def FDsolver(
        xmin, xmax, n, fval, Hcoeff,
        correction=False,
        neighbors=2):
    """

    Builds an FD matrix for the equation system
    u''(x) = f(x)*u(x)

    Sets up the structure of H as in terms of the standard FD stencil
    of -1/2*LAPLACIAN

    Solves this using the sparse scipy solver or with numpy's eigenvalue solver

    Args:
        xmin (float): lower end of domain
        xmax(float): upper end of domain
        n (int): number of points
        fval (object): function for 'RHS'
        Hcoeff (float):coefficient to multiply the FD matrix with
        neighbours -- order of FD solver
            (higher convergence for more neighbours)

    Returns:
        eigenvalue spectrum (numpy array)
    """
    # Insure tha the bounds are properly defined
    assert xmax > xmin

    # Distance between grid points
    h = (xmax-xmin)/(n - 1.0)

    # The grid array and source term
    potential = np.zeros(n)
    x0 = np.zeros(n)
    for i in range(n):
        x0[i] = xmin + i*h
        potential[i] = fval(x0[i])

    # Initialization of Main Matrix
    H = np.zeros((n, n))
    for i, c in enumerate(lapbli[neighbors]):
        H.flat[n * i::n + 1] = -0.5 * c / h**2
        H.flat[i:n*(n-i)+1:n + 1] = -0.5 * c / h**2

    # Setting boundary correction of H using modified
    # FD stencil of -1/2*LAPLACIAN of the same order
    if correction:
        corrstencil = np.array(boundarycorr[neighbors])
        lencorr = len(corrstencil)

        # Fixing the first and last row first
        H.flat[0:lencorr-1] = -0.5 * corrstencil[1:] / h**2
        H.flat[-(lencorr-1):] = -0.5 * (corrstencil[1:])[::-1]/h**2

        # All the in between rows
        for i in range(1, neighbors-1):
            H.flat[n*i:n*i+lencorr] = -0.5*corrstencil / h**2
            H.flat[-n*i-lencorr:-n*i] = -0.5*corrstencil[::-1] / h**2
            corrstencil = np.insert(corrstencil, [0], 0.)
            lencorr = len(corrstencil)
    # Correcting units of hamiltonian
    # Standard is units._hbar**2/(2*units._amu*modemass*1e-20*units._e)
    H *= Hcoeff

    # Adding the potential
    H += np.diag(potential)

    if not correction:
        # H symmetric, eigenvalues are real
        eigenvaluesrough = np.linalg.eigvalsh(H)
        eigenvalues = np.sort(eigenvaluesrough)
    else:
        # H not symmetric -> eigenvalues could have imaginary component,
        # careful here..
        eigenvaluesrough = np.linalg.eigvals(H)
        eigenvalues = np.sort(np.abs(eigenvaluesrough))

    return eigenvalues


def ConvergenceExponent(new, newer, newest, increment):
    exponent = np.log((new-newer)/(newer-newest))/np.log(increment)  # If a==b
    return exponent


def RichardsonExtrapolator(approximantarray, realincrementfactor, order=2):
    length = len(approximantarray)
    richardsonextrapolant = np.zeros(length)
    richardsonconvexponents = np.zeros(length)
    for r in range(1, length):
        richardsonextrapolant[r] = (
            approximantarray[r]
            + (
                (approximantarray[r] - approximantarray[r-1])
                / (realincrementfactor**order - 1)))
        if r > 2:
            richardsonconvexponents[r] = (
                ConvergenceExponent(
                    richardsonextrapolant[r-2], richardsonextrapolant[r-1],
                    richardsonextrapolant[r], realincrementfactor))
    return richardsonextrapolant, richardsonconvexponents


def RombergIntegrator(integrants, realincrementfactor=2, exact=None):
    extrapolants = np.zeros((len(integrants), len(integrants)))
    convexps = np.zeros((len(integrants), len(integrants)))
    relativeerrors = np.zeros((len(integrants), len(integrants)))
    extrapolants[0, :] = integrants
    for i in range(1, len(integrants)):
        extr, convexp = RichardsonExtrapolator(
            extrapolants[i-1, i-1:], realincrementfactor, order=2*i)
    extrapolants[i, i-1:] = extr
    if exact is None:
        bestextrap = extrapolants[len(integrants)-1, len(integrants)-1]
    else:
        bestextrap = exact
    for i in range(len(integrants)):
        for j in range(i+1, len(integrants)):
            convexps[i, j] = (
                np.log(
                    (bestextrap-extrapolants[i, j-1])
                    / (bestextrap-extrapolants[i, j]))
                / np.log(realincrementfactor))
    for i in range(len(integrants)):
        for j in range(i, len(integrants)):
            relativeerrors[i, j] = int(
                np.log(
                    np.abs(1-extrapolants[i, j]/(bestextrap+1e-24)))
                / np.log(10))
    bestdiaelement = 0

    i = 1
    while i < len(integrants) and abs(convexps[i-1, i]-2.0*i) < 2.0:
        bestdiaelement = i
        i += 1

    bestextrapolantvalue = extrapolants[bestdiaelement, bestdiaelement]
    errestimate = int(
        np.log(np.abs((
            extrapolants[bestdiaelement-1, bestdiaelement-1]
            - extrapolants[bestdiaelement-1, bestdiaelement])
            / (extrapolants[bestdiaelement-1, bestdiaelement]+1e-24)+1e-24))
        / np.log(10))
    return (
        extrapolants, relativeerrors, convexps,
        bestextrapolantvalue, errestimate)


def RombergSpectrumIntegrator(spectrum, realincrementfactor=2):
    extrapolatedspectrum = np.zeros(len(spectrum[0, :]))
    relativeerrors = np.zeros(len(spectrum[0, :]))
    for i in range(len(spectrum[0, :])):
        rombergeigenvals, relerr, convexps, best, besterr = RombergIntegrator(
            spectrum[:, i], realincrementfactor)
        extrapolatedspectrum[i] = best
        relativeerrors[i] = besterr
    return extrapolatedspectrum, relativeerrors





#
#  Other
#
#

# def RombergSpectrumIntegrator(spectrum, realincrementfactors):
#     """
#     Args:
#         Spectrum (numpy array): energies from energy solver
#         realincrementfactors (float): how much to increment grid with
#     return;
#         extrapolatedspectrum (numpy array): Improved energy spectra
#         relativeerrors (numpy array): Error estimates
#     """
#     # Number of points used to solve the initial equation
#     n = len(spectrum[0, :])

#     extrapolatedspectrum = np.zeros(n)
#     relativeerrors = np.zeros(n)
#     for i in range(n):
#         rombergeigenvals, relerr, convexps, best, besterr = \
#             RombergIntegrator(spectrum[:, i], realincrementfactors[0])
#         extrapolatedspectrum[i] = best
#         relativeerrors[i] = besterr
#     return extrapolatedspectrum, relativeerrors


# def RombergIntegrator(integrants, realincrementfactor=2, exact=None):
#     """"""
#     n = len(integrants)

#     extrapolants = np.zeros((n, n))
#     convexps = np.zeros((n, n))
#     relativeerrors = np.zeros((n, n))

#     extrapolants[0, :] = integrants
#     for i in range(1, n):
#         extr, convexp = \
#             RichardsonExtrapolator(
#                 extrapolants[i-1, i-1:], realincrementfactor, order=2*i)
#     extrapolants[i, i-1:] = extr

#     if exact is None:
#         bestextrap = extrapolants[n-1, n-1]
#     else:
#         bestextrap = exact

#     for i in range(n):
#         for j in range(i+1, n):
#             pre = bestextrap-extrapolants[i, j-1]
#             aft = bestextrap-extrapolants[i, j]
#             # It is normal to get a runtime error here during the first run
#             # which we can happily ignore
#             with np.errstate(invalid='ignore'):
#                 convexps[i, j] = np.log(pre/aft)/np.log(realincrementfactor)

#     for i in range(n):
#         for j in range(i, n):
#             relativeerrors[i, j] = (
#                 int(np.log(np.abs(1-extrapolants[i, j]/(bestextrap+1e-24)))
#                     / np.log(10)))

#     bestdiaelement = 0
#     i = 1
#     while i < n and abs(convexps[i-1, i]-2.0*i) < 2.0:
#         i += 1
#     bestdiaelement = i-1

#     bestextrapolantvalue = extrapolants[bestdiaelement, bestdiaelement]

#     tmp1 = (
#         extrapolants[bestdiaelement-1, bestdiaelement-1]
#         - extrapolants[bestdiaelement-1, bestdiaelement])
#     tmp2 = extrapolants[bestdiaelement-1, bestdiaelement]+1e-24
#     errestimate = int(np.log(np.abs(tmp1/tmp2+1e-24))/np.log(10))
#     return (
#         extrapolants, relativeerrors, convexps,
#         bestextrapolantvalue, errestimate)


# def RichardsonExtrapolator(approxarr, factor, order=2):
#     """"""
#     length = len(approxarr)
#     extrapolant = np.zeros(length)
#     exponents = np.zeros(length)
#     for r in range(1, length):
#         extrapolant[r] = (
#             approxarr[r]+(approxarr[r]-approxarr[r-1])/(factor**order-1))
#         if r > 2:
#             exponents[r] = ConvergenceExponent(
#                 extrapolant[r-2], extrapolant[r-1], extrapolant[r], factor)
#     return extrapolant, exponents


# def ConvergenceExponent(new, newer, newest, increment):
#     """"""
#     exponent = np.log((new-newer)/(newer-newest))/np.log(increment)
#     return exponent
