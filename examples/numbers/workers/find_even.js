var poliglo = require('poliglo'),
    path = require('path');

var process_func = function(specific_info, data, callback, options){
    try{
        var inputs = poliglo.inputs.get_inputs(data, specific_info);
        var return_values = [];
        if(inputs.number % 2 === 0)
            return_values = [inputs,];    //is even
        callback(null, return_values);
    }catch(err){
        callback(err, []);
    }
};

poliglo.runner.default_main(
    process.env.POLIGLO_SERVER_URL,
    path.basename(__filename, path.extname(__filename)),
    process_func
);
