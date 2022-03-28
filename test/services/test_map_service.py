from services import map_service


def test_gets_correct_number_of_unique_maps():
    maps = map_service.get_maps(num_maps=4)

    assert len(set(maps)) == 4


def test_can_exclude_maps():
    original_map = map_service.get_maps(num_maps=1)[0]
    new_maps = map_service.get_maps(num_maps=10, exclude={original_map})

    assert len(set(new_maps)) == 10
    assert original_map not in new_maps


def test_weighting():
    for i in range(20):
        result = map_service.get_maps(num_maps=1)
        print(result)
