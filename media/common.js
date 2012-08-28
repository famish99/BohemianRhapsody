function getURLVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,
        function(m, key, value) {
            vars[key] = value;
        });
    return vars;
}

function setURLVars(parms) {
    var str = "?";
    for(var key in parms){
        str += key + '=' + parms[key] + '&';
    }
    if(str == '?'){
        return str;
    }
    return str.slice(0, str.length - 1);
}
