def classFactory(iface):
    from .walk_distance_calculator import WalkDistanceCalculator
    return WalkDistanceCalculator(iface)