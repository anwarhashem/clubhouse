from gi.repository import Gdk, GdkPixbuf, Gtk, GObject


def gtk_widget_add_custom_css_provider(widget, for_screen=False,
                                       priority=Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1):
    css_provider = Gtk.CssProvider()
    context = widget.get_style_context()
    if not for_screen:
        context.add_provider(css_provider, priority)
    else:
        context.add_provider_for_screen(Gdk.Screen.get_default(), css_provider, priority)
    return css_provider


class FixedLayerGroup(Gtk.Bin):

    __gtype_name__ = 'FixedLayerGroup'
    __dummy_layer_attr__ = '__{}LayerName'.format(__gtype_name__)

    def __init__(self):
        super().__init__()

        self._layers = {}
        self._overlay = Gtk.Overlay(halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)

        self.add(self._overlay)

    def get_children(self):
        return self._overlay.get_children()

    def add_layer(self, widget, layer_name):
        if layer_name in self._layers:
            return self._layers[layer_name]

        layer = self._new_layer_from_widget(widget)
        self._layers[layer_name] = layer

        self._overlay.add_overlay(layer)
        self._overlay.set_overlay_pass_through(layer, True)

        return layer

    def get_layer(self, layer_name):
        return self._layers.get(layer_name)

    def _new_layer_from_widget(self, widget):
        if isinstance(widget, Gtk.Fixed):
            fixed = widget
        else:
            fixed = Gtk.Fixed()
            fixed.put(widget, 0, 0)

        fixed.props.halign = Gtk.Align.FILL
        fixed.props.valign = Gtk.Align.FILL

        return fixed


class ScalableImage(Gtk.Box):

    __gtype_name__ = 'ScalableImage'

    def __init__(self, path):
        super().__init__()
        image_info = GdkPixbuf.Pixbuf.get_file_info(path)
        if image_info[0] is None or image_info.width == 0 or image_info.height == 0:
            raise IOError('Image file \'{}\' does not exist or unsupported format.'.format(path))

        self.aspect_ratio = image_info.width / image_info.height

        self._css_provider = gtk_widget_add_custom_css_provider(self)

        css = "ScalableImage {{ background-image: url('{}') }}".format(path)
        self._css_provider.load_from_data(css.encode())

    def do_get_request_mode(self):
        return Gtk.SizeRequestMode.HEIGHT_FOR_WIDTH

    def do_get_preferred_height_for_width(self, width):
        height = width / self.aspect_ratio
        return height, height


@Gtk.Template.from_resource('/com/hack_computer/Clubhouse/breadcrumb-button.ui')
class BreadcrumbButton(Gtk.Box):

    __gtype_name__ = 'BreadcrumbButton'

    _back_box = Gtk.Template.Child()
    _back_button = Gtk.Template.Child()
    _back_image = Gtk.Template.Child()
    _inactive_button = Gtk.Template.Child()
    _main_button = Gtk.Template.Child()
    _popover_button = Gtk.Template.Child()
    _popover_button_image = Gtk.Template.Child()
    _popover_revealer = Gtk.Template.Child()
    _popover_label = Gtk.Template.Child()

    def __init__(self):
        super().__init__(self)
        self._active = True
        self._main_button_label = ''
        self._main_popover_label = ''
        self._popup_handler = None
        self._main_popup_handler = None

    def set_popover_button_visible(self, visible):
        self._popover_button.props.visible = visible

    def set_back_actions_visible(self, visible):
        self._back_button.props.visible = visible
        self._back_image.props.visible = visible

    def _popover_toggled_cb(self, widget, prop):
        if widget.props.visible:
            self._popover_button_image.props.icon_name = 'go-up-symbolic'
            self._popover_revealer.set_reveal_child(True)
        else:
            self._popover_button_image.props.icon_name = 'go-down-symbolic'
            self._popover_revealer.set_reveal_child(False)

    def _get_popover(self):
        return self._popover_button.get_popover()

    def _set_popover(self, value):
        if self._popup_handler:
            self._popover_button.props.popover.disconnect(self._popup_handler)
            self._popup_handler = None

        self._popover_button.props.visible = bool(value)
        if value is None:
            return

        self._popup_handler = value.connect('notify::visible',
                                            self._popover_toggled_cb)

        self._popover_button.set_popover(value)
        self._popover_button.show_all()

    def _main_popover_toggled_cb(self, widget, prop):
        if widget.props.visible:
            self._main_button.props.label = self._main_popover_label
            self._main_button.props.always_show_image = False
        else:
            self._main_button.props.label = self._main_button_label
            self._main_button.props.always_show_image = True

    def _get_main_popover(self):
        return self._main_button.get_popover()

    def _set_main_popover(self, value):
        if self._main_popup_handler:
            self._main_button.props.popover.disconnect(self._main_popup_handler)
            self._main_popup_handler = None

        if value:
            self._main_popup_handler = value.connect('notify::visible',
                                                     self._main_popover_toggled_cb)

            self._main_button.set_popover(value)
            self._main_button.show_all()

    def _get_action_name(self):
        return self._main_button.get_action_name()

    def _set_action_name(self, value):
        self._main_button.set_action_name(value)
        self._inactive_button.set_action_name(value)

    def _get_action_target(self):
        return self._main_button.get_action_target_value()

    def _set_action_target(self, value):
        self._main_button.set_action_target_value(value)
        self._inactive_button.set_action_target_value(value)

    def _get_label(self):
        return self._main_button_label

    def _set_label(self, value):
        self._main_button_label = value
        self._main_button.set_label(value)

    def _get_icon_name(self):
        return self._main_button.props.image.get_icon_name

    def _set_icon_name(self, value):
        self._main_button.props.image = Gtk.Image(icon_name=value)
        self._main_button.props.image.props.valign = Gtk.Align.CENTER
        self._inactive_button.props.image = Gtk.Image(icon_name=value)
        self._inactive_button.props.image.props.valign = Gtk.Align.CENTER

    def _get_popover_label(self):
        return self._popover_label.get_label()

    def _set_popover_label(self, value):
        self._popover_label.set_label(value)

    def _get_main_popover_label(self):
        return self._main_popover_label

    def _set_main_popover_label(self, value):
        self._main_popover_label = value

    def get_active(self):
        return self._active

    def set_active(self, value):
        self._active = value

        # to make it a circle the width should be the same as the height
        height = self._main_button.get_allocated_height()
        self._inactive_button.set_size_request(height, height)

        if not self.back_label:
            self._back_box.hide()

        if value:
            self._inactive_button.hide()
            self._main_button.show()
            if self._get_popover():
                self._popover_button.show()
            if self.back_label:
                self._back_box.show()
        else:
            self._inactive_button.show()
            self._main_button.hide()
            if self._get_popover():
                self._popover_button.hide()
            if self.back_label:
                self._back_box.hide()

    def _get_back_label(self):
        return self._back_button.get_label()

    def _set_back_label(self, value):
        self._back_button.set_label(value)

    def _get_back_icon_name(self):
        return self._back_button.props.image.get_icon_name

    def _set_back_icon_name(self, value):
        self._back_button.props.image = Gtk.Image(icon_name=value)
        self._back_button.props.image.props.valign = Gtk.Align.CENTER

    def _get_back_action_name(self):
        return self._back_button.get_action_name()

    def _set_back_action_name(self, value):
        self._back_button.set_action_name(value)

    def _get_back_action_target(self):
        return self._back_button.get_action_target_value()

    def _set_back_action_target(self, value):
        self._back_button.set_action_target_value(value)

    main_popover = GObject.Property(_get_main_popover,
                                    _set_main_popover,
                                    type=GObject.TYPE_OBJECT)
    main_popover_label = GObject.Property(_get_main_popover_label,
                                          _set_main_popover_label,
                                          type=str)
    popover = GObject.Property(_get_popover, _set_popover, type=GObject.TYPE_OBJECT)
    popover_label = GObject.Property(_get_popover_label, _set_popover_label, type=str)
    action_name = GObject.Property(_get_action_name, _set_action_name, type=str)
    action_target = GObject.Property(_get_action_target,
                                     _set_action_target,
                                     type=GObject.TYPE_VARIANT)
    label = GObject.Property(_get_label, _set_label, type=str)
    icon_name = GObject.Property(_get_icon_name, _set_icon_name, type=str)
    back_label = GObject.Property(_get_back_label, _set_back_label, type=str)
    back_icon_name = GObject.Property(_get_back_icon_name, _set_back_icon_name, type=str)
    back_action_name = GObject.Property(_get_back_action_name,
                                        _set_back_action_name,
                                        type=str)
    back_action_target = GObject.Property(_get_back_action_target,
                                          _set_back_action_target,
                                          type=GObject.TYPE_VARIANT)
    active = GObject.Property(get_active, set_active, type=bool, default=True)


class PopoverListRow(Gtk.ListBoxRow):

    __gtype_name__ = 'PopoverListRow'

    def __init__(self, popover_list, data_item_id, has_image):
        super().__init__(halign=Gtk.Align.FILL, visible=True)
        self.popover_list = popover_list
        self.id = data_item_id

        box = Gtk.Box(visible=True)
        self.add(box)

        if self.icon_name is not None:
            image = Gtk.Image(visible=True, icon_name=self.icon_name, icon_size=Gtk.IconSize.MENU)
            box.add(image)

        label = Gtk.Label(visible=True, halign=Gtk.Align.START, label=self.title)
        box.add(label)

    def _get_title(self):
        return self.popover_list.data[self.id][0]

    def _get_icon_name(self):
        if not self.popover_list.has_image:
            return None
        return self.popover_list.data[self.id][1]

    title = property(_get_title)
    icon_name = property(_get_icon_name)


class PopoverList(Gtk.Popover):

    # __gtype_name__ not set because totally shadows Gtk.Popover style.
    __widget_name__ = 'PopoverList'

    def __init__(self, has_image=False, disable_selected_row=True,
                 **kwargs):
        super().__init__(name=self.__widget_name__, **kwargs)
        self._popover_list_box = Gtk.ListBox(activate_on_single_click=True, visible=True)
        self.add(self._popover_list_box)

        self.has_image = has_image
        self._selected_item_id = None

        # key: id, value: list of data
        self._data = {}
        self._rows = {}
        self._list_store = None

        self._popover_list_box.connect('row-activated', self._popover_list_box_row_activated_cb)
        if disable_selected_row:
            self.connect('notify::selected-item-id', self._notify_selected_item_id_cb)

    def _add_item(self, data_item_id):
        row = PopoverListRow(self, data_item_id, self.has_image)
        self._popover_list_box.add(row)
        return row

    def _popover_list_box_row_activated_cb(self, _list_box, row):
        self.props.selected_item_id = row.id

    def _notify_selected_item_id_cb(self, *_args):
        for row in self._popover_list_box.get_children():
            row.props.sensitive = row.id != self.props.selected_item_id

    def _set_selected_item_id(self, value):
        if self._selected_item_id != value:
            self._selected_item_id = value
            self.notify('selected-item-id')

    def _get_selected_item_id(self):
        return self._selected_item_id

    def _set_list_store(self, list_store):
        for row in list_store:
            id_, *tail = row[:]
            self._data[id_] = tail
            self._rows[id_] = self._add_item(id_)
        self._list_store = list_store

    def _get_list_store(self):
        return self._list_store

    def _get_data(self):
        return self._data

    def _get_selected_row(self):
        return self._rows.get(self.props.selected_item_id)

    selected_item_id = GObject.Property(_get_selected_item_id, _set_selected_item_id, type=str,
                                        flags=(GObject.ParamFlags.READWRITE |
                                               GObject.ParamFlags.EXPLICIT_NOTIFY))
    selected_row = property(_get_selected_row)
    list_store = GObject.Property(_get_list_store, _set_list_store, type=object)
    data = property(_get_data)


@Gtk.Template.from_resource('/com/hack_computer/Clubhouse/selector-widget.ui')
class SelectorWidget(Gtk.Box):

    __gtype_name__ = 'SelectorWidget'

    _title_label = Gtk.Template.Child()
    _close_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._list_store = None
        self._selected_item_id = None
        self.popover = PopoverList(relative_to=self)

        self.bind_property('list-store', self.popover, 'list-store', GObject.BindingFlags.DEFAULT)
        self.popover.bind_property('selected-item-id', self, 'selected-item-id',
                                   GObject.BindingFlags.BIDIRECTIONAL)

    def _selected_item_id_to_css_class(self, selected_item_id=None):
        return selected_item_id.lower().replace(' ', '')

    def _setup_unselected_state(self):
        self._title_label.props.label = self.props.default_label
        self._title_label.props.halign = Gtk.Align.CENTER
        self._close_button.props.visible = False
        ctx = self.get_style_context()
        ctx.remove_class('selected')
        if self._selected_item_id is not None:
            ctx.remove_class(self._selected_item_id_to_css_class(self._selected_item_id))

    def _setup_selected_state(self, new_selected_item_id):
        self._title_label.props.label = self.popover.selected_row.title
        self._title_label.props.halign = Gtk.Align.START
        self._close_button.props.visible = True
        ctx = self.get_style_context()
        ctx.add_class('selected')
        if self._selected_item_id is not None:
            ctx.remove_class(self._selected_item_id_to_css_class(self._selected_item_id))
        if new_selected_item_id is not None:
            ctx.add_class(self._selected_item_id_to_css_class(new_selected_item_id))

    @Gtk.Template.Callback()
    def _title_button_clicked_cb(self, _button):
        self.popover.popup()
        self.popover.show_all()

    @Gtk.Template.Callback()
    def _close_button_clicked_cb(self, _button):
        self.props.selected_item_id = None

    def _set_default_label(self, label):
        self._title_label.props.label = label
        self._default_label = label

    def _get_default_label(self):
        return self._default_label

    def _set_selected_item_id(self, value):
        if value is not None:
            self._setup_selected_state(value)
        else:
            self._setup_unselected_state()
        self.popover.popdown()
        self._selected_item_id = value

    def _get_selected_item_id(self):
        return self._selected_item_id

    default_label = GObject.Property(_get_default_label, _set_default_label, type=str)
    selected_item_id = GObject.Property(_get_selected_item_id, _set_selected_item_id, type=str)
    list_store = GObject.Property(type=object)


# Set widget classes CSS name to be able to select by GType name
widgets_classes = [
    BreadcrumbButton,
    FixedLayerGroup,
    PopoverListRow,
    ScalableImage,
    SelectorWidget
]

for klass in widgets_classes:
    klass.set_css_name(klass.__gtype_name__)
