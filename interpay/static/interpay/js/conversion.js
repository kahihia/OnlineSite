/**
 * Created by Arman on 12/27/2016.
 //  */

function convert(amount, index, from_code) {
    var currency_select = document.getElementById("currency_code" + index);
    var converted = document.getElementById("converted" + index);
    $.ajax({
        url: "/wallets/convert_currency/", // the endpoint
        type: "GET", // http method
        data: {from_code: from_code, to_code: currency_select.value, amount: amount}, // data sent with the post request

        // handle a successful response
        success: function (json) {
            converted.innerHTML = json['result'];
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}