
const St = imports.gi.St;
const Main = imports.ui.main;
const MessageTray = imports.ui.messageTray;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;
const Lang = imports.lang;
const GLib = imports.gi.GLib;
const Gio = imports.gi.Gio;

const Gettext = imports.gettext.domain('gnome-shell-extensions');
const _ = Gettext.gettext;

const Mainloop = imports.mainloop;
const DBus = imports.dbus;

function DeviceItem() {
    this._init.apply(this, arguments);
}

DeviceItem.prototype = {
    __proto__: PopupMenu.PopupBaseMenuItem.prototype,

    _init: function(device) {
        PopupMenu.PopupBaseMenuItem.prototype._init.call(this, { reactive: false });

        let [name, path, num] = device;

        this._box = new St.BoxLayout({ style_class: 'popup-device-menu-item' });
        this._label = new St.Label({ text: name });

        this._box.add_actor(this._label);
        this.addActor(this._box);

        this._percentLabel = new St.Label();
        this.addActor(this._percentLabel, { align: St.Align.END });
        
        this._lightnessLabel = new St.Label();
        this.addActor(this._lightnessLabel, { align: St.Align.END });
        
        this._lightnessTimeoutId = 0;
    },
    
    setLightness: function(v){
    	if(v==null){
    		this._lightnessLabel.text = C_("no lightness data", "");
    	} else {
    		this._lightnessLabel.text = C_("lightness in lux", "%d lux").format(v);
    		
    		if(this._lightnessTimeoutId > 0){
    			Mainloop.source_remove(this._lightnessTimeoutId);
    		}
    			
    		this._lightnessTimeoutId = Mainloop.timeout_add(2000, Lang.bind(this, function(){
				this.setLightness();
    		}));
    	}
    },
    setCharge: function(v){
    	this._percentLabel.text = C_("percent of battery remaining", "%d%%").format(v);
    }
}


function SolarMenu() {
	
	const PySolarInterface = {
	    name: 'pl.glorpen.PySolar',
	    methods: [
	              { name: 'ListDevices', inSignature: '', outSignature: 'a{ssi}' }
	    ],
	    signals: [
			{ name: "ChargeEvent", inSignature: 'suu'},
			{ name: "LightnessEvent", inSignature: 'suuu'},
			{ name: "DevicesChangedEvent", inSignature: ''}
	    ]
	};

	var PySolarProxy = DBus.makeProxyClass(PySolarInterface);
	var solar = new PySolarProxy(DBus.system, 'pl.glorpen.PySolar', '/pl/glorpen/PySolar');
	
	var chargeCallback = Lang.bind(this, function(emitter, device, num, charge, lightness){
		this._updateDevice(this._deviceItems[[device, num]], charge, lightness);
	});
	
	var reloadDevices = Lang.bind(this, function(){
		solar.ListDevicesRemote(Lang.bind(this, function(result, err){
			if(err!=null){
				throw new Error(err);
			} else {
				let devices = {};
				for(var i in result){
					var r=result[i];
					devices[[r[1],r[2]]]=new DeviceItem(r);
				}
				
				this._addDevices(devices);
			}
		}));
	});
	
	solar.connect("LightnessEvent", chargeCallback);
	solar.connect("ChargeEvent", chargeCallback);
	solar.connect("DevicesChangedEvent", reloadDevices);
	
	this.reloadDevices = reloadDevices;
	
    this._init.apply(this, arguments);
}
 
SolarMenu.prototype = {
	__proto__: PanelMenu.SystemStatusButton.prototype,
	_deviceItems: {},
 
    _init: function() {
    	PanelMenu.SystemStatusButton.prototype._init.call(this, 'input-keyboard-symbolic');
    	
    	this.reloadDevices();
    },
    
    _addDevices: function(devices){
    	for(var i in this._deviceItems){
    		this._deviceItems[i].destroy();
    	}
    	
    	for(var key in devices){
    		this.menu.addMenuItem(this._deviceItems[key]=devices[key]);
    	}
    },
    
    _updateDevice: function(device, charge, lightness){
    	device.setCharge(charge);
    	device.setLightness(lightness);
    },
};

function init(metadata) {
    imports.gettext.bindtextdomain('gnome-shell-extensions', GLib.build_filenamev([metadata.path, 'locale']));
}

let _indicator;

function enable() {
	_indicator = new SolarMenu;
    Main.panel.addToStatusArea('solar-menu', _indicator);
}

function disable() {
    _indicator.destroy();
}
