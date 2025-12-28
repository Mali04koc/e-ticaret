$('.plus-cart').click(function () {
    console.log('Button clicked')

    var id = $(this).attr('pid').toString()
    // var quantity = this.parentNode.children[2] // This was selecting the button (index 2) resulting in overwrite!

    $.ajax({
        type: 'GET',
        url: '/pluscart',
        data: {
            cart_id: id
        },

        success: function (data) {
            console.log(data)
            // quantity.innerText = data.quantity // FIX: Don't use the wrong selector
            document.getElementById(`quantity${id}`).innerText = data.quantity
            document.getElementById('amount_tt').innerText = data.amount
            document.getElementById('totalamount').innerText = data.total

        }
    })
})


$('.minus-cart').click(function () {
    console.log('Button clicked')

    var id = $(this).attr('pid').toString()
    // var quantity = this.parentNode.children[2] // Incorrect selector (Index 2 is plus button!)

    var currentQuantity = parseInt(document.getElementById(`quantity${id}`).innerText);

    if (currentQuantity > 1) {
        $.ajax({
            type: 'GET',
            url: '/minuscart',
            data: {
                cart_id: id
            },

            success: function (data) {
                console.log(data)
                // quantity.innerText = data.quantity 
                document.getElementById(`quantity${id}`).innerText = data.quantity
                document.getElementById('amount_tt').innerText = data.amount
                document.getElementById('totalamount').innerText = data.total

            }
        })
    }
})


$('.remove-cart').click(function () {

    var id = $(this).attr('pid').toString()

    var to_remove = this.parentNode.parentNode.parentNode.parentNode

    $.ajax({
        type: 'GET',
        url: '/removecart',
        data: {
            cart_id: id
        },

        success: function (data) {
            document.getElementById('amount_tt').innerText = data.amount
            document.getElementById('totalamount').innerText = data.total
            to_remove.remove()
        }
    })


})
