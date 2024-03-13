import React, { useCallback, useEffect, useState } from 'react';
import TagsInput from 'react-tagsinput';
import 'react-tagsinput/react-tagsinput.css';
import Dropzone from 'react-dropzone'
import axios from 'axios';

const CreateProduct = (props) => {
    const [productName, setProductName] = useState("")
    const [productSku, setProductSku] = useState("")
    const [description, setDescription] = useState("")
    const [productVariantPrices, setProductVariantPrices] = useState([])
    const [mediaFiles, setFiles] = useState([])
    const [productVariants, setProductVariant] = useState([
        {
            option: 1,
            tags: []
        }
    ])

    const fetchProductData = useCallback(async (id) => {
        const response = await axios.get(`/product/api/update/${id}/`)
        if (response.status == 200) {
            const data = response.data
            console.log(data.title)
            setProductName(data.title)
            setProductSku(data.sku)
            setDescription(data.description)
            const productVariantsNew = [
                {
                    option: 1,
                    tags: data.variants.filter(value => value.variant == 1).map(value => value.variant_title)
                },
                {
                    option: 2,
                    tags: data.variants.filter(value => value.variant == 2).map(value => value.variant_title)
                },
                {
                    option: 3,
                    tags: data.variants.filter(value => value.variant == 3).map(value => value.variant_title)
                }
            ]
            setProductVariant(productVariantsNew)
            const variant_prices = data.variant_prices.map(item => {
                const variantOne = data.variants.find(value => value.id == item.product_variant_one)?.variant_title
                const variantTwo = data.variants.find(value => value.id == item.product_variant_two)?.variant_title
                const variantThree = data.variants.find(value => value.id == item.product_variant_three)?.variant_title

                return {
                    id: item.id,
                    title: `${variantOne ?? ""}/${variantTwo ?? ""}/${variantThree ?? ""}`,
                    price: item.price,
                    stock: item.stock
                }
            })

            setProductVariantPrices(variant_prices)


        }
    }, [])

    useEffect(() => {
        if (window.location.pathname.split("/")[3] != null && window.location.pathname.split("/")[3] != undefined) {
            const id = window.location.pathname.split("/")[3]
            if (id) {
                fetchProductData(id)
            }
        }
    }, [window])
    // handle click event of the Add button
    const handleAddClick = () => {
        let all_variants = JSON.parse(props.variants.replaceAll("'", '"')).map(el => el.id)
        let selected_variants = productVariants.map(el => el.option);
        let available_variants = all_variants.filter(entry1 => !selected_variants.some(entry2 => entry1 == entry2))
        setProductVariant([...productVariants, {
            option: available_variants[0],
            tags: []
        }])
    };

    // handle input change on tag input
    const handleInputTagOnChange = (value, index) => {
        let product_variants = [...productVariants]
        product_variants[index].tags = value
        setProductVariant(product_variants)

        checkVariant()
    }

    // remove product variant
    const removeProductVariant = (index) => {
        let product_variants = [...productVariants]
        product_variants.splice(index, 1)
        setProductVariant(product_variants)
    }

    // check the variant and render all the combination
    const checkVariant = () => {
        let tags = [];

        productVariants.filter((item) => {
            tags.push(item.tags)
        })

        setProductVariantPrices([])

        getCombn(tags).forEach(item => {
            setProductVariantPrices(productVariantPrice => [...productVariantPrice, {
                title: item,
                price: 0,
                stock: 0
            }])
        })
    }

    // handle input change on price input
    const handlePriceChange = (value, index) => {
        let updatedPrices = [...productVariantPrices];
        updatedPrices[index].price = parseFloat(value) || 0;
        setProductVariantPrices(updatedPrices);
    }

    // handle input change on stock input
    const handleStockChange = (value, index) => {
        let updatedPrices = [...productVariantPrices];
        updatedPrices[index].stock = parseInt(value) || 0;
        setProductVariantPrices(updatedPrices);
    }

    // combination algorithm
    function getCombn(arr, pre) {
        pre = pre || '';
        if (!arr.length) {
            return pre;
        }
        let ans = arr[0].reduce(function (ans, value) {
            return ans.concat(getCombn(arr.slice(1), pre + value + '/'));
        }, []);
        return ans;
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (const element of cookies) {
                const cookie = element.trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Save product
    let saveProduct = (event) => {
        event.preventDefault();


        const formData = new FormData();


        formData.append('name', productName);
        formData.append('sku', productSku);
        formData.append('description', description);

        // Append variants
        formData.append('variants', JSON.stringify(productVariants));

        // Append variantPrices
        formData.append('variantPrices', JSON.stringify(productVariantPrices));

        // Append media files
        mediaFiles.forEach((file, index) => {
            formData.append(`media_${index}`, file);
        });


        const csrftoken = getCookie('csrftoken');
        if (window.location.pathname.split("/")[3] != null && window.location.pathname.split("/")[3] != undefined){
            formData.append('id', window.location.pathname.split("/")[3]);
        }
        try {
            
            const response = axios.post("/product/api/create_product/", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'X-CSRFToken': csrftoken,
                },
            })
            if (response.status == 200) {
                console.log(response)
            }
        } catch (error) {
            console.log(error)
        }

    }


    return (
        <div>
            <section>
                <div className="row">
                    <div className="col-md-6">
                        <div className="card shadow mb-4">
                            <div className="card-body">
                                <div className="form-group">
                                    <label htmlFor="">Product Name</label>
                                    <input value={productName} onChange={(e) => setProductName(e.target.value)} type="text" placeholder="Product Name" className="form-control" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="">Product SKU</label>
                                    <input value={productSku} onChange={(e) => setProductSku(e.target.value)} type="text" placeholder="Product Name" className="form-control" />
                                </div>
                                <div className="form-group">
                                    <label htmlFor="">Description</label>
                                    <textarea value={description} onChange={(e) => setDescription(e.target.value)} cols="30" rows="4" className="form-control"></textarea>
                                </div>
                            </div>
                        </div>

                        <div className="card shadow mb-4">
                            <div
                                className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                <h6 className="m-0 font-weight-bold text-primary">Media</h6>
                            </div>
                            <div className="card-body border">
                                <Dropzone onDrop={acceptedFiles => setFiles(acceptedFiles)}>
                                    {({ getRootProps, getInputProps }) => (
                                        <section>
                                            <div {...getRootProps()}>
                                                <input {...getInputProps()} />
                                                <p>Drag 'n' drop some files here, or click to select files</p>
                                            </div>
                                        </section>
                                    )}
                                </Dropzone>
                            </div>
                        </div>
                    </div>

                    <div className="col-md-6">
                        <div className="card shadow mb-4">
                            <div
                                className="card-header py-3 d-flex flex-row align-items-center justify-content-between">
                                <h6 className="m-0 font-weight-bold text-primary">Variants</h6>
                            </div>
                            <div className="card-body">

                                {
                                    productVariants.map((element, index) => {
                                        return (
                                            <div className="row" key={index}>
                                                <div className="col-md-4">
                                                    <div className="form-group">
                                                        <label htmlFor="">Option</label>
                                                        <select className="form-control" defaultValue={element.option}>
                                                            {
                                                                JSON.parse(props.variants.replaceAll("'", '"')).map((variant, index) => {
                                                                    return (<option key={index}
                                                                        value={variant.id}>{variant.title}</option>)
                                                                })
                                                            }

                                                        </select>
                                                    </div>
                                                </div>

                                                <div className="col-md-8">
                                                    <div className="form-group">
                                                        {
                                                            productVariants.length > 1
                                                                ? <label htmlFor="" className="float-right text-primary"
                                                                    style={{ marginTop: "-30px" }}
                                                                    onClick={() => removeProductVariant(index)}>remove</label>
                                                                : ''
                                                        }

                                                        <section style={{ marginTop: "30px" }}>
                                                            <TagsInput value={element.tags}
                                                                style="margin-top:30px"
                                                                onChange={(value) => handleInputTagOnChange(value, index)} />
                                                        </section>

                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })
                                }


                            </div>
                            <div className="card-footer">
                                {productVariants.length !== 3
                                    ? <button className="btn btn-primary" onClick={handleAddClick}>Add another
                                        option</button>
                                    : ''
                                }

                            </div>

                            <div className="card-header text-uppercase">Preview</div>
                            <div className="card-body">
                                <div className="table-responsive">
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <td>Variant</td>
                                                <td>Price</td>
                                                <td>Stock</td>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {productVariantPrices.map((productVariantPrice, index) => {
                                                return (
                                                    <tr key={index}>
                                                        <td>{productVariantPrice.title}</td>
                                                        <td>
                                                            <input
                                                                className="form-control"
                                                                type="text"
                                                                value={productVariantPrice.price}
                                                                onChange={(e) => handlePriceChange(e.target.value, index)}
                                                            />
                                                        </td>
                                                        <td>
                                                            <input
                                                                className="form-control"
                                                                type="text"
                                                                value={productVariantPrice.stock}
                                                                onChange={(e) => handleStockChange(e.target.value, index)}
                                                            />
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <button type="button" onClick={saveProduct} className="btn btn-lg btn-primary">Save</button>
                <button type="button" className="btn btn-secondary btn-lg">Cancel</button>
            </section>
        </div>
    );
};

export default CreateProduct;
