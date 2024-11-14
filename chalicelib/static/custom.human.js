/**
 * EC2 QuickLook Frontend JavaScript
 * Handles UI interactions and data fetching for EC2 instance and volume information
 */

// Initialize the application namespace
const EC2QuickLook = {
    // Cache DOM elements
    elements: {},
    
    // Cache for selected instance type
    selectedType: 'm5.xlarge',
    
    // Default instance families
    defaultFamilies: ['m5', 'm6g'],

    /**
     * Initialize the application
     */
    init() {
        this.cacheElements();
        this.bindEvents();
        this.updateTypes();
    },

    /**
     * Cache frequently used DOM elements
     */
    cacheElements() {
        this.elements = {
            arch: $('#arch'),
            region: $('#region'),
            family: $('#family'),
            types: $('#types'),
            btnQuery: $('#btnquery'),
            forms: document.getElementsByClassName('needs-validation')
        };
    },

    /**
     * Bind event handlers
     */
    bindEvents() {
        // Form validation
        this.setupFormValidation();
        
        // Input change handlers
        this.elements.arch.on('change', () => this.updateFamily());
        this.elements.region.on('change', () => {
            this.selectedType = this.elements.types.val();
            this.updateTypes();
        });
        this.elements.family.on('change', () => this.updateTypes());
        
        // Query button handler
        this.elements.btnQuery.on('click', () => {
            this.queryInstance();
            this.queryVolume();
        });
    },

    /**
     * Setup Bootstrap form validation
     */
    setupFormValidation() {
        Array.prototype.filter.call(this.elements.forms, (form) => {
            form.addEventListener('submit', (event) => {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    },

    /**
     * Update instance family options based on selected architecture
     */
    updateFamily() {
        const region = this.elements.region.val();
        const arch = this.elements.arch.val();

        $.ajax({
            url: "instance/family",
            data: { region, arch },
            dataType: "json",
            beforeSend: () => this.showLoading(this.elements.family),
            success: (result) => {
                let familyOptions = ["<option value=''>Choose...</option>"];
                
                result.forEach(item => {
                    const isDefault = this.defaultFamilies.includes(item.name);
                    familyOptions.push(
                        `<option ${isDefault ? 'selected' : ''} value="${item.name}">
                            ${item.description}: ${item.name}
                        </option>`
                    );
                    if (isDefault) this.updateTypes(item.name);
                });

                this.elements.family.html(familyOptions.join(''));
            },
            error: (xhr, status, error) => {
                console.error('Failed to fetch instance families:', error);
                this.showError('Failed to load instance families');
            },
            complete: () => this.hideLoading(this.elements.family)
        });
    },

    /**
     * Update instance types based on selected family
     * @param {string} [family] - Optional family parameter
     */
    updateTypes(family) {
        const params = {
            region: this.elements.region.val(),
            arch: this.elements.arch.val(),
            family: family || this.elements.family.val()
        };

        $.ajax({
            url: "instance/types",
            data: params,
            dataType: "json",
            beforeSend: () => this.showLoading(this.elements.types),
            success: (result) => {
                let typeOptions = ["<option value=''>Choose...</option>"];
                let unmatch = true;

                result.forEach(item => {
                    const isSelected = item.instanceType === this.selectedType;
                    typeOptions.push(
                        `<option ${isSelected ? 'selected' : ''} value="${item.instanceType}">
                            ${item.instanceType}
                        </option>`
                    );
                    if (isSelected) unmatch = false;
                });

                this.elements.types.html(typeOptions.join(''));
                if (unmatch) this.elements.types.prop("selectedIndex", 1);
            },
            error: (xhr, status, error) => {
                console.error('Failed to fetch instance types:', error);
                this.showError('Failed to load instance types');
            },
            complete: () => this.hideLoading(this.elements.types)
        });
    },

    /**
     * Query instance information
     */
    queryInstance() {
        const params = {
            region: this.elements.region.val(),
            type: this.elements.types.val(),
            op: $('#operation').val()
        };

        $.ajax({
            url: "product/instance",
            data: params,
            dataType: "json",
            beforeSend: () => this.showLoading($('#instance')),
            success: (result) => this.updateInstanceUI(result),
            error: (xhr, status, error) => {
                console.error('Failed to fetch instance data:', error);
                this.showError('Failed to load instance information');
            },
            complete: () => this.hideLoading($('#instance'))
        });
    },

    /**
     * Query volume information
     */
    queryVolume() {
        const params = {
            region: this.elements.region.val(),
            type: $('#voltypes').val(),
            size: $('#volsize').val()
        };

        $.ajax({
            url: "product/volume",
            data: params,
            dataType: "json",
            beforeSend: () => this.showLoading($('#tbvolspec')),
            success: (result) => this.updateVolumeUI(result),
            error: (xhr, status, error) => {
                console.error('Failed to fetch volume data:', error);
                this.showError('Failed to load volume information');
            },
            complete: () => this.hideLoading($('#tbvolspec'))
        });
    },

    /**
     * Update instance information UI
     * @param {Object} result - Instance data
     */
    updateInstanceUI(result) {
        if ("listPrice" in result) {
            $('#insprice').html(`${result.listPrice.pricePerUnit.currency} ${result.listPrice.pricePerUnit.value.toFixed(2)}`);
            $('#insunit').html(result.listPrice.unit);
            $('#insdate').html(result.listPrice.effectiveDate);
            $('#insfamily').html(result.productMeta.instanceFamily);
            $('#instenan').html(result.productMeta.tenancy);
            $('#insloca').html(result.productMeta.location);
            $('#insurl').attr('href', result.productMeta.introduceUrl);
            $('#tbdetail').show();
            $('#detailurl').attr('href', `detail?region=${this.elements.region.val()}&type=${this.elements.types.val()}`);
        } else {
            this.resetInstanceUI();
        }

        this.updateTable('#tbhardware', result.hardwareSpecs);
        this.updateTable('#tbsoftware', result.softwareSpecs);
        this.updateTable('#tbinstorage', result.instanceSotrage);
        this.updateTable('#tbfeature', result.productFeature);
    },

    /**
     * Update volume information UI
     * @param {Object} result - Volume data
     */
    updateVolumeUI(result) {
        this.updateTable('#tbvolspec', result.productSpecs);
        
        $('#volprice').html(`${result.listPrice.pricePerUnit.currency} ${result.listPrice.pricePerUnit.value.toFixed(2)}`);
        $('#volunit').html(result.listPrice.unit);
        $('#voldate').html(result.listPrice.effectiveDate);
        $('#voltype').html(result.productMeta.volumeType);
        $('#usagetype').html(result.productMeta.usagetype);
        $('#volmedia').html(result.productMeta.storageMedia);
        $('#volurl').attr('href', result.productMeta.introduceUrl);
    },

    /**
     * Reset instance UI to default state
     */
    resetInstanceUI() {
        $('#insprice').html('unknown');
        $('#insunit').html('Month');
        $('#insdate').html('');
        $('#insfamily').html('Not Found');
        $('#instenan').html('');
        $('#insloca').html('');
        $('#insurl').attr('href', '');
        $('#tbdetail').hide();
    },

    /**
     * Update table content
     * @param {string} tableId - Table selector
     * @param {Object} data - Table data
     */
    updateTable(tableId, data) {
        const rows = Object.entries(data).map(([key, value]) => 
            `<tr><td>${key}</td><td>${value}</td></tr>`
        );
        $(tableId).html(rows.join(''));
    },

    /**
     * Show loading indicator
     * @param {jQuery} element - jQuery element
     */
    showLoading(element) {
        element.addClass('loading').prop('disabled', true);
    },

    /**
     * Hide loading indicator
     * @param {jQuery} element - jQuery element
     */
    hideLoading(element) {
        element.removeClass('loading').prop('disabled', false);
    },

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        console.error(message);
    }
};

// Initialize application when DOM is ready
$(function() {
    EC2QuickLook.init();
});
