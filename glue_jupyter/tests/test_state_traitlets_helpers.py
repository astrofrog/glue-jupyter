import traitlets
from glue.core import Data
from glue.core.state_objects import State, CallbackProperty
from echo import ListCallbackProperty
import glue_jupyter as gj
from glue_jupyter.state_traitlets_helpers import GlueState, update_state_from_dict


class Widget1(traitlets.HasTraits):

    state = GlueState()

    latest_json = None

    # The following two methods mimic the behavior of ipywidgets

    @traitlets.observe('state')
    def on_state_change(self, change):
        to_json = self.trait_metadata('state', 'to_json')
        self.latest_json = to_json(self.state, self)

    def set_state_from_json(self, json):
        from_json = self.trait_metadata('state', 'from_json')
        from_json(json, self)


class CustomSubState(State):
    c = CallbackProperty(3)


class CustomState(State):
    a = CallbackProperty(1)
    b = CallbackProperty(2)
    sub = ListCallbackProperty()


def test_to_json():
    widget = Widget1()
    assert widget.latest_json is None
    widget.state = CustomState()
    assert widget.latest_json == {"a": 1, "b": 2, "sub": []}
    widget.state.sub.append(CustomSubState())
    assert widget.latest_json == {"a": 1, "b": 2, "sub": [{"c": 3}]}
    widget.state.sub[0].c = 4
    assert widget.latest_json == {"a": 1, "b": 2, "sub": [{"c": 4}]}
    widget.state.b = 5
    assert widget.latest_json == {"a": 1, "b": 5, "sub": [{"c": 4}]}
    widget.state.sub.pop(0)
    assert widget.latest_json == {"a": 1, "b": 5, "sub": []}


def test_from_json():
    widget = Widget1()
    widget.state = CustomState()
    widget.state.sub.append(CustomSubState())
    assert widget.latest_json == {"a": 1, "b": 2, "sub": [{"c": 3}]}
    widget.set_state_from_json({"a": 3})
    assert widget.state.a == 3
    assert widget.latest_json == {"a": 3, "b": 2, "sub": [{"c": 3}]}
    widget.set_state_from_json({"sub": [{"c": 2}]})
    assert widget.state.sub[0].c == 2
    assert widget.latest_json == {"a": 3, "b": 2, "sub": [{"c": 2}]}
    # Giving an empty list does not clear the list - it just means that no
    # items will be updated.
    widget.set_state_from_json({"sub": []})
    assert widget.latest_json == {"a": 3, "b": 2, "sub": [{"c": 2}]}
    # We can also update lists by passing a dict with index: value pairs in
    # cases where we just want to update some values
    widget.set_state_from_json({"sub": {0: {'c': 9}}})
    assert widget.latest_json == {"a": 3, "b": 2, "sub": [{"c": 9}]}


def test_to_json_data():
    # Make sure we just convert the dataset to its label
    widget = Widget1()
    widget.state = CustomState()
    widget.state.a = Data(label='test')
    assert widget.latest_json == {"a": "611cfa3b-ebb5-42d2-b5c7-ba9bce8b51a4",
                                  "b": 2,
                                  "sub": []}


def test_from_json_nested_ignore():
    # Regression test for a bug that cause the MAGIC_IGNORE value to be set on
    # the glue state if it existed in a nested structure.
    widget = Widget1()
    widget.state = CustomState()
    widget.state.sub.append(CustomSubState())
    widget.state.sub[0].c = Data(label='test')
    widget.state.sub.append(Data(label='test'))
    assert widget.latest_json == {"a": 1,
                                  "b": 2,
                                  "sub": [{'c': '611cfa3b-ebb5-42d2-b5c7-ba9bce8b51a4'},
                                          '611cfa3b-ebb5-42d2-b5c7-ba9bce8b51a4']}
    widget.set_state_from_json(widget.latest_json)
    assert widget.state.a == 1
    assert widget.state.b == 2
    assert isinstance(widget.state.sub[0].c, Data)
    assert isinstance(widget.state.sub[1], Data)


def test_update_state_from_dict_no_stale_overwrite():
    # Regression test: when update_state_from_dict receives a dict with
    # both a high-priority property and lower-priority properties whose
    # values match the current state, the lower-priority properties
    # should not be applied if a callback from the high-priority property
    # has since changed them.
    #
    # Real-world example: the browser sends {x_log: True, x_min: -10,
    # x_max: 30}. Setting x_log triggers _reset_x_limits which updates
    # x_min/x_max to positive values. Without the fix, the stale -10/30
    # would then overwrite the corrected values because they now differ
    # from the callback-updated state.

    app = gj.jglue()
    data = app.add_data(data={'x': [-10, -5, 0, 5, 15, 30],
                               'y': [5, 10, 20, 35, 40, 50]})[0]
    viewer = app.scatter2d(data=data)
    state = viewer.state

    assert state.x_min < 0

    stale_x_min = state.x_min
    stale_x_max = state.x_max

    # Simulate what the browser sends: x_log changed, but x_min/x_max
    # are stale (unchanged from the browser's perspective)
    update_state_from_dict(state, {
        'x_log': True,
        'x_min': stale_x_min,
        'x_max': stale_x_max,
    })

    # x_min/x_max should have been reset to positive values by the
    # x_log callback, and NOT overwritten by the stale values
    assert state.x_min > 0
    assert state.x_max > 0
